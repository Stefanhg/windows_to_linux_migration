"""Prove the acceptance suite detects Cinnamon's original monitor split."""
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree
from gi.repository import Gio

sys.path.insert(0, str(Path(__file__).parent / 'features'))
from desktop import cinnamon, eventually

settings = Gio.Settings.new('org.cinnamon')
original = settings.get_strv('enabled-extensions')
extension = 'mirrored-panels@fix-mint'
assert extension in original, 'Run on a working deployment with mirroring enabled'

def monitor_lists():
    return cinnamon('''return imports.ui.appletManager.getRunningInstancesForUuid('grouped-window-list@cinnamon.org')
        .map(a=>a.state.monitorWatchList);''')

report = Path('tests/reports/negative-control')
try:
    settings.set_strv('enabled-extensions', [name for name in original if name != extension])
    Gio.Settings.sync()
    eventually(lambda: len(monitor_lists()) == 2 and all(len(m) == 1 for m in monitor_lists()),
               'original per-monitor filtering after disabling mirroring')
    result = subprocess.run([
        sys.executable, '-m', 'behave', 'tests/features', '--name',
        "An application's window", '--junit', '--junit-directory', str(report),
    ], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    print(result.stdout)
    cases = [case for xml in report.glob('*.xml') for case in ElementTree.parse(xml).iter('testcase')
             if case.find('failure') is not None]
    assert result.returncode == 1 and len(cases) == 2, 'Expected both monitor scenarios to fail'
    assert all('visible test-window entry in both live task lists' in ''.join(case.itertext()) for case in cases), \
        'Must fail on actual missing window entries, not setup errors'
finally:
    settings.set_strv('enabled-extensions', original)
    Gio.Settings.sync()
    eventually(lambda: len(monitor_lists()) == 2 and all(len(m) >= 2 for m in monitor_lists()),
               'restored mirrored taskbars')

print('Regression sensitivity verified: both scenarios caught the broken behavior; mirroring restored.')
