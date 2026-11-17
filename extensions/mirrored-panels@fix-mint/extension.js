const Main = imports.ui.main;
const Mainloop = imports.mainloop;
let timer = null;
let originals = new Map();
let previousPins = new Map();
let sharedPins = null;

function mirrorMonitors() {
    const monitorWatchList = Array.from({length: global.display.get_n_monitors()}, (_, i) => i);
    this.state.set({monitorWatchList});
}

function synchronize() {
    const instances = Main.AppletManager.getRunningInstancesForUuid('grouped-window-list@cinnamon.org') || [];
    for (const applet of instances) {
        if (!originals.has(applet)) {
            originals.set(applet, applet.updateMonitorWatchlist);
            applet.updateMonitorWatchlist = mirrorMonitors;
            applet.updateMonitorWatchlist();
            applet.refreshAllAppLists();
        }
    }
    // A changed pin list on either panel becomes the shared list. New panels
    // inherit the current list instead of replacing it with their defaults.
    for (const applet of instances) {
        const pins = applet.settings.getValue('pinned-apps');
        const encoded = JSON.stringify(pins);
        if (sharedPins === null || (previousPins.has(applet) && previousPins.get(applet) !== encoded)) {
            sharedPins = pins.slice();
        }
    }
    for (const applet of instances) {
        const encoded = JSON.stringify(sharedPins);
        if (JSON.stringify(applet.settings.getValue('pinned-apps')) !== encoded) {
            applet.settings.setValue('pinned-apps', sharedPins.slice());
            applet.pinnedFavorites.reload();
            applet.refreshAllAppLists();
        }
        previousPins.set(applet, encoded);
    }
    for (const applet of originals.keys()) {
        if (!instances.includes(applet)) {
            originals.delete(applet);
            previousPins.delete(applet);
        }
    }
    return true;
}

function init() {}

function enable() {
    synchronize();
    timer = Mainloop.timeout_add_seconds(1, synchronize);
}

function disable() {
    if (timer !== null) Mainloop.source_remove(timer);
    timer = null;
    for (const [applet, original] of originals) {
        applet.updateMonitorWatchlist = original;
        applet.updateMonitorWatchlist();
        applet.refreshAllAppLists();
    }
    originals.clear();
    previousPins.clear();
    sharedPins = null;
}
