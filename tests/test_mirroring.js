// Run from the project root: cjs tests/test_mirroring.js
const Gio = imports.gi.Gio;
const ByteArray = imports.byteArray;
const path = 'extensions/mirrored-panels@fix-mint/extension.js';
const [, contents] = Gio.File.new_for_path(path).load_contents(null);
function assert(value, message) { if (!value) throw new Error(message); }
function applet(pins) {
    return {
        pins, monitors: [], refreshes: 0,
        state: {set(value) { this.owner.monitors = value.monitorWatchList; }},
        updateMonitorWatchlist() { this.monitors = [0]; },
        refreshAllAppLists() { this.refreshes++; },
        settings: {
            getValue() { return this.owner.pins; },
            setValue(key, value) { this.owner.pins = value; }
        },
        pinnedFavorites: {reload() {}}
    };
}
const first = applet(['browser.desktop']);
const second = applet(['terminal.desktop']);
for (const item of [first, second]) {
    item.state.owner = item;
    item.settings.owner = item;
}
const original = first.updateMonitorWatchlist;
let instances = [first, second];
let tick, removed = false, monitorCount = 2;
const fakeImports = {
    ui: {main: {AppletManager: {getRunningInstancesForUuid() {return instances;}}}},
    mainloop: {
        timeout_add_seconds(seconds, callback) {tick = callback; return 1;},
        source_remove() {removed = true;}
    }
};
const extension = new Function('imports', 'global', ByteArray.toString(contents) +
    '\nreturn {enable, disable};')(fakeImports, {display: {get_n_monitors() {return monitorCount;}}});
extension.enable();
assert(JSON.stringify(first.monitors) === '[0,1]', 'primary must show both monitors');
assert(JSON.stringify(second.monitors) === '[0,1]', 'secondary must show both monitors');
assert(second.pins[0] === 'browser.desktop', 'secondary inherits primary pins');
second.pins = ['editor.desktop'];
tick();
assert(first.pins[0] === 'editor.desktop', 'secondary pin changes propagate');
first.pins = ['files.desktop'];
tick();
assert(second.pins[0] === 'files.desktop', 'primary pin changes propagate');
monitorCount = 3;
first.updateMonitorWatchlist();
assert(JSON.stringify(first.monitors) === '[0,1,2]', 'new monitors are included');
extension.disable();
assert(removed && first.updateMonitorWatchlist === original, 'disable restores original behavior and removes timer');
assert(JSON.stringify(first.monitors) === '[0]', 'monitor filtering restored');
print('Mirroring tests passed');
