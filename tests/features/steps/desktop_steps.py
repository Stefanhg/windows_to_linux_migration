import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from behave import given, when, then
from desktop import cinnamon, eventually, Input, taskbars, with_window, window_state


@given('a running Cinnamon X11 desktop with two monitors')
def desktop_ready(context):
    assert os.environ.get('XDG_SESSION_TYPE') == 'x11', 'Requires Cinnamon X11; Wayland input is not supported'
    assert cinnamon('return global.display.get_n_monitors();') >= 2, 'Connect two monitors; this is a failure, not a skip'
    context.bars = taskbars()
    assert len(context.bars) == 2 and {b['monitor'] for b in context.bars} == {0, 1}, 'Expected one grouped task list per monitor'


@then('each monitor has a visible taskbar 60 logical pixels tall')
def panel_size(context):
    panels = cinnamon('''
        return imports.ui.main.panelManager.getPanels().filter(p=>p && p.actor.visible)
            .map(p=>({monitor:p.monitorIndex,height:p.actor.height/global.ui_scale}));
    ''')
    for monitor in (0, 1):
        assert any(p['monitor'] == monitor and p['height'] == 60 for p in panels), panels


@given('a new application window')
def new_window(context):
    context.title = 'Mint acceptance ' + uuid.uuid4().hex
    context.window_process = subprocess.Popen([sys.executable, str(Path(__file__).parents[1] / 'test_window.py'), context.title])
    eventually(lambda: window_state(context.title), 'test application window')
    with_window(context.title, 'w.activate(global.get_current_time()); return true;')


@when('I move the application window to monitor {monitor:d}')
def move_window(context, monitor):
    with_window(context.title, f'w.move_to_monitor({monitor}); return true;')
    eventually(lambda: window_state(context.title)['monitor'] == monitor, f'window on monitor {monitor}')


@then('the actual application window appears in both taskbars')
def mirrored_window(context):
    def visible():
        bars = taskbars()
        return len(bars) == 2 and all(any(g['visible'] and context.title in g['windows'] for g in b['groups']) for b in bars)
    eventually(visible, 'visible test-window entry in both live task lists')


@when('I pin an installed application on taskbar {panel:d}')
def pin_app(context, panel):
    bars = taskbars()
    assert bars[0]['pins'] == bars[1]['pins'], 'Start with synchronized pins so cleanup can restore them safely'
    context.saved_pins = bars[0]['pins']
    apps = cinnamon('''return imports.gi.Gio.AppInfo.get_all().map(a=>a.get_id())
        .filter(id => id && imports.gi.Cinnamon.AppSystem.get_default().lookup_app(id));''')
    context.app_id = next((app for app in apps if app not in context.saved_pins), None)
    assert context.app_id, 'Need an installed, unpinned application'
    # Invoke the same action as the real applet context menu; no settings-file edits.
    cinnamon('''
        const a=imports.ui.appletManager.getRunningInstancesForUuid('grouped-window-list@cinnamon.org')
            .slice().sort((a,b)=>a.panel.monitorIndex-b.panel.monitorIndex)[PANEL];
        a.pinnedFavorites.addFavorite({appId:APP}); return true;
    '''.replace('PANEL', str(panel)).replace('APP', json.dumps(context.app_id)))


@then('its launcher appears on both taskbars')
def mirrored_pin(context):
    eventually(lambda: all(any(g['id'] == context.app_id and g['pinned'] and g['visible'] for g in bar['groups'])
                          for bar in taskbars()), 'visible pinned launcher on both panels')


@when('I drag its title bar to the top of the monitor')
def drag_window(context):
    with_window(context.title, 'w.unmaximize(3); w.move_to_monitor(0); w.move_resize_frame(true, 200, 200, 640, 400); w.activate(global.get_current_time()); return true;')
    def positioned():
        state = window_state(context.title)
        if state and state['monitor'] == 0 and not state['maximized'] and state['rect'] == {'x':200, 'y':200, 'width':640, 'height':400}:
            return state
        return None
    state = eventually(positioned, 'test window configure event before dragging')
    rect = state['rect']
    monitor = cinnamon('return imports.ui.main.layoutManager.monitors[0];')
    context.input = Input()
    context.input.drag((rect['x'] + rect['width']/2, rect['y'] + 12),
                       (monitor['x'] + monitor['width']/2, monitor['y']))


@then('the window fills the monitor work area')
def maximized(context):
    def fills():
        state = window_state(context.title)
        return state['maximized'] == 3 and all(abs(state['rect'][k]-state['area'][k]) <= 2 for k in ('x','y','width','height'))
    eventually(fills, 'full maximization after an actual title-bar drag')


@when('I press Windows Shift S')
def screenshot_keys(context):
    context.input = Input()
    context.before_overlays = context.input.overlays()
    assert not context.before_overlays, 'Close the existing Flameshot overlay before testing'
    context.capture_requested = True
    context.input.chord('Super_L', 'Shift_L', 's')


@then('a new Flameshot capture overlay is visible')
def screenshot_overlay(context):
    eventually(lambda: context.input.overlays() - context.before_overlays, 'Flameshot capture window after real Win+Shift+S input')


@then('the sound menu remains closed')
def sound_closed(context):
    assert cinnamon('''return imports.ui.appletManager.getRunningInstancesForUuid('sound@cinnamon.org')
        .every(a => !a.menu.isOpen);'''), 'Sound menu opened instead of capture'
