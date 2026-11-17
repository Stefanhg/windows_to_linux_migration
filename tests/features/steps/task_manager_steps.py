import subprocess
from behave import given, when, then
from gi.repository import Gio
from desktop import cinnamon, eventually, Input


def mission_windows():
    return cinnamon('''return global.get_window_actors().filter(a => {
        const w=a.meta_window;
        return ((w.get_gtk_application_id() || '') + ' ' + (w.get_wm_class() || ''))
            .toLowerCase().includes('missioncenter');
    }).map(a=>({sequence:a.meta_window.get_stable_sequence(),visible:a.visible,
        minimized:a.meta_window.minimized,focused:global.display.focus_window === a.meta_window}));''')


@given('Mission Center is installed')
def installed(context):
    subprocess.run(['flatpak', 'info', 'io.missioncenter.MissionCenter'], check=True, capture_output=True)


@given('Mission Center is ready to launch')
def not_open(context):
    context.mission_existing = mission_windows()
    context.mission_launch_requested = True
    cinnamon('''for (const a of global.get_window_actors()) {
        const w=a.meta_window;
        if (((w.get_gtk_application_id() || '') + ' ' + (w.get_wm_class() || '')).toLowerCase().includes('missioncenter'))
            w.minimize();
    } return true;''')


@given('a searchable Task Manager application launcher exists')
def launcher_exists(context):
    launcher = Gio.DesktopAppInfo.new('task-manager.desktop')
    assert launcher and launcher.get_name() == 'Task Manager' and launcher.should_show(), 'Task Manager is missing from application search'


@when('I launch Task Manager')
def launch(context):
    assert Gio.DesktopAppInfo.new('task-manager.desktop').launch([], None), 'Launcher failed'


@when('I press Control Shift Escape')
def shortcut(context):
    context.input = Input()
    context.input.chord('Control_L', 'Shift_L', 'Escape')


@then('a Mission Center window is visible')
def opened(context):
    eventually(lambda: any(w['visible'] and not w['minimized'] and w['focused'] for w in mission_windows()),
               'visible, focused Mission Center window', timeout=30)
