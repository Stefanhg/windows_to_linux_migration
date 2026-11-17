"""Map the README's Task Manager alternative for the current desktop user."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tweaks import get, set_value

APP = 'io.missioncenter.MissionCenter'
COMMAND = 'flatpak run ' + APP


def apply():
    if os.geteuid() == 0:
        raise RuntimeError('Run as your desktop user, without sudo.')
    if not shutil.which('flatpak'):
        raise RuntimeError('Flatpak is required to install and launch Mission Center.')
    installed = subprocess.run(['flatpak', 'info', APP], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if installed.returncode:
        subprocess.run(['flatpak', 'install', '--noninteractive', 'flathub', APP], check=True)
    schema = 'org.cinnamon.desktop.keybindings'
    name = 'migration-task-manager'
    target = schema + '.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/' + name + '/'
    names = get(schema, 'custom-list')
    if name in names and get(target, 'command') != COMMAND:
        raise RuntimeError(f'Custom shortcut {name} already belongs to another command.')
    directory = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'applications'
    directory.mkdir(parents=True, exist_ok=True)
    launcher = directory / 'task-manager.desktop'
    contents = '''[Desktop Entry]
Type=Application
Name=Task Manager
Comment=View processes and system performance with Mission Center
Exec=flatpak run io.missioncenter.MissionCenter
Icon=io.missioncenter.MissionCenter
Terminal=false
Categories=System;Monitor;
Keywords=Task;Manager;Mission;Center;Processes;CPU;Memory;
StartupNotify=true
'''
    if launcher.exists() and launcher.read_text() != contents:
        raise RuntimeError(f'Refusing to replace an unrelated launcher: {launcher}')
    launcher.write_text(contents)
    for key, value in [('name', 'Task Manager'), ('command', COMMAND),
                       ('binding', ['<Primary><Shift>Escape'])]:
        set_value(target, key, value)
    if name not in names:
        set_value(schema, 'custom-list', names + [name])
    print('Task Manager launcher and Ctrl+Shift+Esc now open Mission Center.')


if __name__ == '__main__':
    try:
        apply()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
