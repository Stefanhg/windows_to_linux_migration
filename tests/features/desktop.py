"""Desktop driver. No imports from tweaks.py and no mocked Cinnamon objects."""
import json
import time
from gi.repository import Gio, GLib
from Xlib import X, XK, display
from Xlib.ext import xtest


def cinnamon(body):
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    result = bus.call_sync(
        'org.Cinnamon', '/org/Cinnamon', 'org.Cinnamon', 'Eval',
        GLib.Variant('(s)', ('(() => {try {' + body + '} catch (e) {return {__test_error:String(e),stack:e.stack};}})()',)),
        GLib.VariantType.new('(bs)'), Gio.DBusCallFlags.NONE, 5000, None)
    success, value = result.unpack()
    assert success, f'Cinnamon evaluation failed: {value}'
    decoded = json.loads(value) if value else None
    assert not (isinstance(decoded, dict) and '__test_error' in decoded), decoded
    return decoded


def eventually(check, description, timeout=8):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = check()
        if last:
            return last
        time.sleep(0.1)
    raise AssertionError(f'Timed out waiting for {description}; last result: {last!r}')


def taskbars():
    return cinnamon('''
        return imports.ui.appletManager.getRunningInstancesForUuid('grouped-window-list@cinnamon.org')
            .slice().sort((a,b) => a.panel.monitorIndex-b.panel.monitorIndex)
            .map(a => ({id:a.instance_id, monitor:a.panel.monitorIndex,
                pins:a.settings.getValue('pinned-apps'),
                groups:a.getCurrentAppList().appList.map(g => ({
                    id:g.groupState.appId, pinned:g.groupState.isFavoriteApp,
                    visible:g.actor.visible,
                    windows:g.groupState.metaWindows.map(w => w.get_title())
                }))}));
    ''')


def with_window(title, action):
    return cinnamon('''
        const w = global.get_window_actors().map(a => a.meta_window)
            .find(w => w.get_title() === TITLE);
        if (!w) return null;
    '''.replace('TITLE', json.dumps(title)) + action)


def window_state(title):
    return with_window(title, '''
        const r=w.get_frame_rect(), area=w.get_work_area_current_monitor();
        return {monitor:w.get_monitor(), maximized:w.get_maximized(),
            rect:{x:r.x,y:r.y,width:r.width,height:r.height},
            area:{x:area.x,y:area.y,width:area.width,height:area.height}};
    ''')


class Input:
    def __init__(self):
        self.connection = display.Display()
        self.pointer = self.connection.screen().root.query_pointer()

    def key(self, name, pressed):
        code = self.connection.keysym_to_keycode(XK.string_to_keysym(name))
        assert code, f'No X11 keycode for {name}'
        xtest.fake_input(self.connection, X.KeyPress if pressed else X.KeyRelease, code)
        self.connection.sync()

    def chord(self, *names):
        pressed = []
        try:
            for name in names:
                self.key(name, True)
                pressed.append(name)
        finally:
            for name in reversed(pressed):
                self.key(name, False)

    def motion(self, x, y):
        xtest.fake_input(self.connection, X.MotionNotify, x=int(x), y=int(y))
        self.connection.sync()

    def drag(self, start, end):
        self.motion(*start)
        xtest.fake_input(self.connection, X.ButtonPress, 1)
        self.connection.sync()
        try:
            for step in range(1, 21):
                self.motion(*(a + (b-a)*step/20 for a,b in zip(start,end)))
                time.sleep(0.03)
            time.sleep(0.5)
        finally:
            xtest.fake_input(self.connection, X.ButtonRelease, 1)
            self.connection.sync()

    def overlays(self):
        # Include override-redirect Qt windows, which may not be in Meta's list.
        result = set()
        for window in self.connection.screen().root.query_tree().children:
            try:
                classes = window.get_wm_class() or ()
                if any('flameshot' in c.lower() for c in classes):
                    attrs = window.get_attributes()
                    geometry = window.get_geometry()
                    if attrs.map_state == X.IsViewable and geometry.width > 300 and geometry.height > 200:
                        result.add(window.id)
            except Exception:
                # A window may disappear while enumerating X11 windows.
                continue
        return result

    def close(self):
        self.motion(self.pointer.root_x, self.pointer.root_y)
        self.connection.close()
