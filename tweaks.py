"""Apply the README's Cinnamon tweaks using the current user's settings."""
import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from collections import Counter

APPLET_DIRECTORY = Path('/usr/share/cinnamon/applets')


def complete_second_panel(panels, applets, next_id):
    """Backfill supported applets on existing panels as well as new ones."""
    template = panels[0].split(':')[0]
    sources = [a.split(':') for a in applets if a.split(':')[0] == 'panel' + template]
    applets = list(applets)
    for panel in panels:
        pid, monitor, _ = panel.split(':')
        if monitor != '1' or pid == template:
            continue
        counts = Counter(a.split(':')[3] for a in applets if a.split(':')[0] == 'panel' + pid)
        occurrences = Counter()
        for source in sources:
            uuid = source[3]
            occurrences[uuid] += 1
            if counts[uuid] >= occurrences[uuid]:
                continue
            metadata = APPLET_DIRECTORY / uuid / 'metadata.json'
            if not metadata.exists():
                continue
            limit = json.loads(metadata.read_text()).get('max-instances', 1)
            total = sum(a.split(':')[3] == uuid for a in applets)
            if limit != -1 and total >= limit:
                continue
            clone = ['panel' + pid, *source[1:4], str(next_id), *source[5:]]
            config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'cinnamon/spices' / uuid
            if len(source) > 4 and (config / (source[4] + '.json')).exists():
                settings = json.loads((config / (source[4] + '.json')).read_text())
                # Per-instance keyboard shortcuts must not compete for the same grab.
                for entry in settings.values():
                    if isinstance(entry, dict) and entry.get('type') == 'keybinding':
                        entry['value'] = ''
                destination = config / f'{next_id}.json'
                if destination.exists():
                    raise RuntimeError(f'Applet configuration already exists: {destination}')
                destination.write_text(json.dumps(settings, indent=4) + '\n')
            applets.append(':'.join(clone))
            next_id += 1
            counts[uuid] += 1
    return applets, next_id


def update_second_panel_applets():
    panels = get('org.cinnamon', 'panels-enabled')
    applets = get('org.cinnamon', 'enabled-applets')
    next_id = max([get('org.cinnamon', 'next-applet-id')] +
                  [int(a.split(':')[4]) + 1 for a in applets if len(a.split(':')) > 4])
    applets, next_id = complete_second_panel(panels, applets, next_id)
    set_value('org.cinnamon', 'next-applet-id', next_id)
    set_value('org.cinnamon', 'enabled-applets', applets)


def release_sound_grab():
    # Cinnamon's addHotKey(name, '') returns before removing the old grab.
    # Clearing the JSON therefore takes effect only after login unless we
    # explicitly release the running applet's grab and register custom keys again.
    script = '''(() => {
        const main = imports.ui.main;
        for (const a of imports.ui.appletManager.getRunningInstancesForUuid('sound@cinnamon.org')) {
            main.keybindingManager.removeHotKey('sound-open-' + a.instance_id);
            a.menu.close();
        }
        main.keybindingManager.on_customs_changed();
        return true;
    })()'''
    result = subprocess.run([
        'gdbus', 'call', '--session', '--dest', 'org.Cinnamon',
        '--object-path', '/org/Cinnamon', '--method', 'org.Cinnamon.Eval', script,
    ], check=True, text=True, capture_output=True, timeout=10)
    if not result.stdout.startswith('(true,'):
        raise RuntimeError('Could not release the active sound shortcut. Log out and back in, then rerun tweaks.sh.')


def disable_sound_hotkey():
    """Sound is a single-instance applet, whose settings use its UUID filename."""
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
    path = config / 'cinnamon/spices/sound@cinnamon.org/sound@cinnamon.org.json'
    if path.exists():
        data = json.loads(path.read_text())
    else:
        source = Path('/usr/share/cinnamon/applets/sound@cinnamon.org/settings-schema.json')
        data = json.loads(source.read_text())
        for entry in data.values():
            if isinstance(entry, dict) and 'default' in entry:
                entry['value'] = entry['default']
    data['keyOpen']['value'] = ''
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = path.with_suffix('.json.before-migration')
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(json.dumps(data, indent=4) + '\n')
    if json.loads(path.read_text())['keyOpen']['value'] != '':
        raise RuntimeError('Sound hotkey was not cleared.')
    release_sound_grab()


def install_mirroring():
    uuid = 'mirrored-panels@fix-mint'
    source = Path(__file__).resolve().parent / 'extensions' / uuid
    destination = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'cinnamon/extensions' / uuid
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('metadata.json', 'extension.js'):
        shutil.copy2(source / name, destination / name)
        if (source / name).read_bytes() != (destination / name).read_bytes():
            raise RuntimeError(f'Extension installation failed: {name}')
    enabled = get('org.cinnamon', 'enabled-extensions')
    if uuid not in enabled:
        set_value('org.cinnamon', 'enabled-extensions', enabled + [uuid])


def get(schema, key):
    value = subprocess.check_output(['gsettings', 'get', schema, key], text=True).strip()
    if value.startswith('@as '):
        value = value[4:]
    return ast.literal_eval(value.replace('true', 'True').replace('false', 'False'))


def set_value(schema, key, value):
    encoded = json.dumps(value) if isinstance(value, bool) else repr(value)
    subprocess.run(['gsettings', 'set', schema, key, encoded], check=True)
    if get(schema, key) != value:
        raise RuntimeError(f'Setting did not persist: {schema} {key}')


def apply():
    if os.geteuid() == 0:
        raise RuntimeError('Run as your desktop user, without sudo.')
    for command in ('gsettings', 'gdbus', 'flameshot'):
        if not shutil.which(command):
            hint = 'Install with: sudo apt install flameshot' if command == 'flameshot' else 'Install with: sudo apt install libglib2.0-bin'
            raise RuntimeError(f'{command} is required. {hint}')
    schema = 'org.cinnamon'
    panels = get(schema, 'panels-enabled')
    if not panels:
        raise RuntimeError('No Cinnamon panel exists to use as a template.')
    # Cinnamon stores monitor indices in panel settings; index 1 is the second screen.
    added = None
    if not any(p.split(':')[1] == '1' for p in panels):
        added = str(max(int(p.split(':')[0]) for p in panels) + 1)
        panels.append(f'{added}:1:bottom')
    applets = get(schema, 'enabled-applets')
    next_id = get(schema, 'next-applet-id')
    existing_ids = [int(a.split(':')[4]) for a in applets if len(a.split(':')) > 4]
    next_id = max([next_id] + [i + 1 for i in existing_ids])
    applets, next_id = complete_second_panel(panels, applets, next_id)
    # Fixed targets based on Mint's 40px panel and 24/28/16px icons.
    heights = get(schema, 'panels-height')
    ids = {p.split(':')[0] for p in panels}
    heights = [h for h in heights if h.split(':')[0] not in ids]
    heights += [f'{pid}:60' for pid in sorted(ids, key=int)]
    updates = {'panels-height': heights, 'enabled-applets': applets,
               'next-applet-id': next_id, 'panels-enabled': panels}
    for key, defaults in [('panel-zone-icon-sizes', (0, 0, 36)),
                          ('panel-zone-symbolic-icon-sizes', (42, 42, 24))]:
        zones = json.loads(get(schema, key))
        for pid in ids:
            zones = [z for z in zones if z['panelId'] != int(pid)]
            zones.append(dict(zip(('panelId', 'left', 'center', 'right'), (int(pid), *defaults))))
        updates[key] = json.dumps(sorted(zones, key=lambda z: z['panelId']))
    shortcuts = 'org.cinnamon.desktop.keybindings'
    custom = shortcuts + '.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/'
    names = get(shortcuts, 'custom-list')
    name = 'migration-flameshot'
    target = custom + name + '/'
    # Do not overwrite an unrelated shortcut that happens to use our chosen name.
    if name in names and get(target, 'command') != 'flameshot gui':
        raise RuntimeError(f'Custom shortcut {name} already belongs to another command.')
    for key, value in updates.items():
        set_value(schema, key, value)
    set_value('org.cinnamon.muffin', 'edge-tiling', True)
    set_value('org.cinnamon.muffin', 'tile-maximize', True)
    disable_sound_hotkey()
    for key, value in [('name', 'Flameshot'), ('command', 'flameshot gui'),
                       ('binding', ['<Super><Shift>s'])]:
        set_value(target, key, value)
    if name not in names:
        names.append(name)
    set_value(shortcuts, 'custom-list', names)
    install_mirroring()
    print('Applied and verified Cinnamon tweaks. The second panel appears when monitor 2 is connected.')


if __name__ == '__main__':
    try:
        apply()
    except (RuntimeError, subprocess.CalledProcessError, ValueError) as error:
        sys.exit(str(error))
