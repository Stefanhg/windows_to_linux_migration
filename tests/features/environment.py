import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
from desktop import cinnamon, eventually, taskbars


def before_scenario(context, scenario):
    context.window_process = None
    context.input = None
    context.saved_pins = None
    context.capture_requested = False
    context.mission_launch_requested = False
    context.mission_existing = []
    context.original_focus = cinnamon('return global.display.focus_window ? global.display.focus_window.get_stable_sequence() : null;')


def after_scenario(context, scenario):
    try:
        if scenario.status == 'failed':
            directory = Path('tests/reports')
            directory.mkdir(parents=True, exist_ok=True)
            (directory / ('failure-' + str(scenario.line) + '.json')).write_text(json.dumps(taskbars(), indent=2))
        if context.input and context.capture_requested and context.input.overlays() - context.before_overlays:
            context.input.chord('Escape')
        if context.saved_pins is not None:
            # Restore all instances to the pre-test shared list, even on failure.
            cinnamon('''
                for (const a of imports.ui.appletManager.getRunningInstancesForUuid('grouped-window-list@cinnamon.org')) {
                    a.settings.setValue('pinned-apps', PINS);
                    a.pinnedFavorites.reload(); a.refreshAllAppLists();
                } return true;
            '''.replace('PINS', json.dumps(context.saved_pins)))
            # Let the asynchronous extension observe restoration before the next
            # scenario changes a pin again. Readback alone is not a barrier.
            stable_since = [None]
            def restored():
                if not all(b['pins'] == context.saved_pins for b in taskbars()):
                    stable_since[0] = None
                    return False
                if stable_since[0] is None:
                    stable_since[0] = time.monotonic()
                return time.monotonic() - stable_since[0] >= 2.2
            eventually(restored, 'restored pins remaining stable across synchronization cycles')
    finally:
        if context.mission_launch_requested:
            cinnamon('''
                const existing=EXISTING;
                for (const a of global.get_window_actors()) {
                    const w=a.meta_window;
                    if (((w.get_gtk_application_id() || '') + ' ' + (w.get_wm_class() || '')).toLowerCase().includes('missioncenter')) {
                        const prior=existing.find(e=>e.sequence === w.get_stable_sequence());
                        if (!prior) w.delete(global.get_current_time());
                        else if (prior.minimized) w.minimize();
                        else w.unminimize();
                    }
                } return true;
            '''.replace('EXISTING', json.dumps(context.mission_existing)))
            eventually(lambda: cinnamon('''const existing=EXISTING; return !global.get_window_actors().some(a => {
                const w=a.meta_window;
                return ((w.get_gtk_application_id() || '') + ' ' + (w.get_wm_class() || '')).toLowerCase().includes('missioncenter')
                    && !existing.some(e=>e.sequence === w.get_stable_sequence());
            });'''.replace('EXISTING', json.dumps(context.mission_existing))), 'test-launched Mission Center window to close')
        if context.window_process:
            context.window_process.terminate()
            context.window_process.wait(timeout=5)
        if context.input:
            context.input.close()
        if context.original_focus is not None:
            cinnamon('''
                const w=global.get_window_actors().map(a=>a.meta_window)
                    .find(w=>w.get_stable_sequence() === SEQUENCE);
                if (w) w.activate(global.get_current_time()); return true;
            '''.replace('SEQUENCE', str(context.original_focus)))
