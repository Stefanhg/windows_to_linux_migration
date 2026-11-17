"""Integration tests: real gsettings, isolated schemas and keyfile backend."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape

spec = importlib.util.spec_from_file_location('tweaks', Path(__file__).resolve().parents[1] / 'tweaks.py')
tweaks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tweaks)


class TweaksTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        applet_directory = root / 'applets'
        for uuid, limit in [('menu@cinnamon.org', -1), ('grouped-window-list@cinnamon.org', -1),
                            ('calendar@cinnamon.org', -1), ('systray@cinnamon.org', 1)]:
            directory = applet_directory / uuid
            directory.mkdir(parents=True)
            (directory / 'metadata.json').write_text(json.dumps({'max-instances': limit}))
        metadata = patch.object(tweaks, 'APPLET_DIRECTORY', applet_directory)
        metadata.start()
        self.addCleanup(metadata.stop)
        definitions = {
            'org.cinnamon': {
                'enabled-extensions': ('as', ['existing-extension']),
                'panels-enabled': ('as', ['1:0:bottom']),
                'panels-height': ('as', ['1:40']),
                'enabled-applets': ('as', ['panel1:left:0:menu@cinnamon.org:0',
                                          'panel1:left:1:grouped-window-list@cinnamon.org:1',
                                          'panel1:right:0:systray@cinnamon.org:2']),
                'next-applet-id': ('i', 3),
                'panel-zone-icon-sizes': ('s', '[{"panelId":1,"left":0,"center":0,"right":24}]'),
                'panel-zone-symbolic-icon-sizes': ('s', '[{"panelId":1,"left":28,"center":28,"right":16}]')},
            'org.cinnamon.muffin': {'edge-tiling': ('b', False), 'tile-maximize': ('b', False)},
            'org.cinnamon.desktop.keybindings': {'custom-list': ('as', ['existing'])},
            'org.cinnamon.desktop.keybindings.custom-keybinding': {
                'name': ('s', ''), 'command': ('s', ''), 'binding': ('as', [])}}
        xml = ['<schemalist>']
        for schema, keys in definitions.items():
            path = '' if schema.endswith('custom-keybinding') else f' path="/{schema.replace(".", "/")}/"'
            xml.append(f'<schema id="{schema}"{path}>')
            for key, (kind, value) in keys.items():
                value = json.dumps(value) if kind == 'b' else repr(value)
                xml.append(f'<key name="{key}" type="{kind}"><default>{escape(value)}</default></key>')
            xml.append('</schema>')
        xml.append('</schemalist>')
        (root / 'test.gschema.xml').write_text(''.join(xml))
        subprocess.run(['glib-compile-schemas', '--strict', str(root)], check=True)
        env = patch.dict(os.environ, GSETTINGS_SCHEMA_DIR=str(root),
                         GSETTINGS_BACKEND='keyfile', XDG_CONFIG_HOME=str(root / 'config'),
                         XDG_DATA_HOME=str(root / 'data'))
        env.start()
        self.addCleanup(env.stop)
        self.uid = patch.object(tweaks.os, 'geteuid', return_value=1000)
        self.uid.start()
        self.addCleanup(self.uid.stop)
        which = patch.object(tweaks.shutil, 'which', return_value='/usr/bin/present')
        which.start()
        self.addCleanup(which.stop)
        # The isolated settings tests must not touch the host keybinding manager;
        # real keyboard grabs are exercised by tests/features/desktop.feature.
        runtime = patch.object(tweaks, 'release_sound_grab')
        runtime.start()
        self.addCleanup(runtime.stop)
        sound = root / 'config/cinnamon/spices/sound@cinnamon.org/sound@cinnamon.org.json'
        sound.parent.mkdir(parents=True)
        sound.write_text(json.dumps({'keyOpen': {'value': '<Shift><Super>s'},
                                     'playerControl': {'value': True}}))

    def test_apply_and_rerun(self):
        tweaks.apply()
        get = tweaks.get
        self.assertEqual(get('org.cinnamon', 'panels-enabled'), ['1:0:bottom', '2:1:bottom'])
        self.assertEqual(get('org.cinnamon', 'panels-height'), ['1:60', '2:60'])
        applets = get('org.cinnamon', 'enabled-applets')
        self.assertIn('panel2:left:1:grouped-window-list@cinnamon.org:4', applets)
        self.assertEqual(len(applets), 5)
        self.assertTrue(get('org.cinnamon.muffin', 'edge-tiling'))
        self.assertTrue(get('org.cinnamon.muffin', 'tile-maximize'))
        for key, right in [('panel-zone-icon-sizes', 36), ('panel-zone-symbolic-icon-sizes', 24)]:
            self.assertEqual([z['right'] for z in json.loads(get('org.cinnamon', key))], [right, right])
        self.assertEqual(get('org.cinnamon.desktop.keybindings', 'custom-list'), ['existing', 'migration-flameshot'])
        custom = 'org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/migration-flameshot/'
        self.assertEqual(get(custom, 'command'), 'flameshot gui')
        self.assertEqual(get(custom, 'binding'), ['<Super><Shift>s'])
        sound = Path(os.environ['XDG_CONFIG_HOME']) / 'cinnamon/spices/sound@cinnamon.org/sound@cinnamon.org.json'
        self.assertEqual(json.loads(sound.read_text())['keyOpen']['value'], '')
        self.assertTrue(json.loads(sound.read_text())['playerControl']['value'])
        self.assertEqual(json.loads(sound.with_suffix('.json.before-migration').read_text())['keyOpen']['value'], '<Shift><Super>s')
        self.assertEqual(get('org.cinnamon', 'enabled-extensions'), ['existing-extension', 'mirrored-panels@fix-mint'])
        installed = Path(os.environ['XDG_DATA_HOME']) / 'cinnamon/extensions/mirrored-panels@fix-mint/extension.js'
        self.assertEqual(installed.read_bytes(), (Path(tweaks.__file__).parent / 'extensions/mirrored-panels@fix-mint/extension.js').read_bytes())
        before = subprocess.check_output(['gsettings', 'list-recursively', 'org.cinnamon'])
        tweaks.apply()
        self.assertEqual(before, subprocess.check_output(['gsettings', 'list-recursively', 'org.cinnamon']))

    def test_existing_second_panel_preserved(self):
        tweaks.set_value('org.cinnamon', 'panels-enabled', ['1:0:bottom', '7:1:top'])
        tweaks.apply()
        self.assertEqual(tweaks.get('org.cinnamon', 'panels-enabled'), ['1:0:bottom', '7:1:top'])

    def test_corrected_shortcut_replaces_previous_control_binding(self):
        custom = 'org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/migration-flameshot/'
        tweaks.set_value('org.cinnamon.desktop.keybindings', 'custom-list', ['existing', 'migration-flameshot'])
        tweaks.set_value(custom, 'command', 'flameshot gui')
        tweaks.set_value(custom, 'binding', ['<Primary><Shift>s'])
        tweaks.apply()
        self.assertEqual(tweaks.get(custom, 'binding'), ['<Super><Shift>s'])

    def test_missing_flameshot_does_not_write(self):
        with patch.object(tweaks.shutil, 'which', return_value=None):
            with self.assertRaises(RuntimeError):
                tweaks.apply()
        self.assertEqual(tweaks.get('org.cinnamon', 'panels-height'), ['1:40'])

    def test_clock_backfilled_on_existing_second_panel_once(self):
        tweaks.set_value('org.cinnamon', 'panels-enabled', ['1:0:bottom', '2:1:bottom'])
        applets = tweaks.get('org.cinnamon', 'enabled-applets')
        applets.append('panel1:right:10:calendar@cinnamon.org:13')
        tweaks.set_value('org.cinnamon', 'enabled-applets', applets)
        config = Path(os.environ['XDG_CONFIG_HOME']) / 'cinnamon/spices/calendar@cinnamon.org'
        config.mkdir(parents=True)
        (config / '13.json').write_text(json.dumps({'custom-format': {'value': '%H:%M'},
                                                   'keyOpen': {'type': 'keybinding', 'value': '<Super>c'}}))
        tweaks.update_second_panel_applets()
        result = tweaks.get('org.cinnamon', 'enabled-applets')
        clocks = [a for a in result if a.startswith('panel2:') and ':calendar@cinnamon.org:' in a]
        self.assertEqual(len(clocks), 1)
        copied = json.loads((config / (clocks[0].split(':')[4] + '.json')).read_text())
        self.assertEqual(copied['custom-format']['value'], '%H:%M')
        self.assertEqual(copied['keyOpen']['value'], '')
        self.assertEqual(sum(':systray@cinnamon.org:' in a for a in result), 1)
        tweaks.update_second_panel_applets()
        self.assertEqual(result, tweaks.get('org.cinnamon', 'enabled-applets'))

    def test_refuses_root(self):
        with patch.object(tweaks.os, 'geteuid', return_value=0):
            with self.assertRaisesRegex(RuntimeError, 'without sudo'):
                tweaks.apply()

    @unittest.skipUnless(Path('/.flatpak-info').exists(), 'Requires a Flatpak environment')
    def test_flatpak_launcher_delegates_to_host(self):
        root = Path(self.tmp.name)
        launcher = root / 'flatpak-spawn'
        launcher.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        launcher.chmod(0o755)
        script = Path(tweaks.__file__).with_suffix('.sh')
        with patch.dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH']):
            result = subprocess.check_output(['sh', str(script)], text=True)
        self.assertEqual(result.splitlines(), ['--host', 'sh', str(script)])


if __name__ == '__main__':
    unittest.main()
