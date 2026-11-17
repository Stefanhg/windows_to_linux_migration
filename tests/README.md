# Desktop acceptance tests

The primary acceptance suite uses [Behave](https://behave.readthedocs.io/en/stable/)
and executable Gherkin scenarios for the [desktop](features/desktop.feature),
[clock](features/clock.feature), and [Task Manager](features/task_manager.feature).
The Python files are desktop automation drivers, not copies of the tweak
implementation. They never import `tweaks.py`, fabricate GSettings schemas,
or replace Cinnamon applets with mocks.

## Setup

Run on Linux Mint 22 Cinnamon **X11**, with two connected monitors and tweaks
already applied. Use a disposable desktop or VM with two virtual displays for
repeatable validation. The suite does not apply tweaks for you: it tests the
desktop as it is, so a broken deployment fails. A plain headless CI runner
cannot provide these guarantees.

Install test dependencies once (from a terminal with Python/pip available):

```sh
python3 -m pip install --target tests/.deps -r tests/requirements-desktop.txt
```

Mint also needs its system packages `python3-gi`, `gir1.2-gtk-3.0`, and
`python3-pip`. The runner uses the system Python so it can load Mint's GTK
bindings. Pure Python test dependencies are isolated in the ignored `.deps`
directory. When launched inside a Flatpak IDE, the runner delegates to the host.

## Running the tests

From the project root:

```sh
sh tests/desktop.sh
sh tests/desktop.sh --name screenshot
sh tests/desktop.sh --tags task-manager
sh tests/desktop.sh --tags clock
sh tests/desktop.sh --dry-run
sh tests/desktop.sh --check-regression
```

Keep your hands off the keyboard and mouse during a run. Tests temporarily
focus a GTK window, change pins, drag its title bar, and open then dismiss the
Flameshot overlay. Cleanup restores the saved pins, focus, and pointer and
terminates only the test-owned application process, including on assertion
failure. Do not run while taking a screenshot yourself. Abrupt process kills
or a Cinnamon crash can prevent cleanup.

## What the suite checks

- Both actual panel actors are visible and 60 logical pixels high.
- A mapped, visible clock label on each panel renders its current time text.
- Mission Center is installed, a searchable Task Manager launcher exists, and
  both that launcher and a real Ctrl+Shift+Esc keypress open a visible Mission
  Center window. An existing Mission Center window is temporarily minimized so
  the test must bring it back and focus it; its state is restored afterward.
  Only newly created Mission Center windows are closed. These two
  scenarios do not require two monitors.
- A real GTK window on either monitor has a visible entry in each task list.
- Pinning through the applet's real action on either panel produces visible
  launchers on both panels. This tests live applet integration; it does not
  automate the context menu's pointer hit targets.
- An XTest mouse drag to the top edge produces both maximize flags and frame
  geometry matching the monitor work area.
- An XTest Win+Shift+S keypress produces a new visible Flameshot capture window
  while the actual sound menu remains closed. It does not save or upload a
  screenshot.

Assertions poll for an observable outcome with a deadline; they do not pass
by reading back the settings that were just written. Missing monitors,
unavailable Cinnamon D-Bus evaluation, or missing desktop prerequisites fail
the run rather than silently skipping acceptance coverage. These tests cover
the grouped-window-list applet and the active workspace; notification-area
duplication and pixel-perfect styling are outside their scope.

## Reports and additional checks

JUnit XML and task-list state on failure go to `tests/reports/`. The older
[test_tweaks.py](test_tweaks.py) and [test_mirroring.js](test_mirroring.js) remain useful fast integration/unit
checks, but passing them alone is not desktop acceptance:

```sh
python3 -m unittest discover -s tests -v
cjs tests/test_mirroring.js
```

`--check-regression` is an optional negative control. It temporarily disables
the mirroring extension, requires both real-window scenarios to fail on
missing task-list entries, and restores the original extension list in a
`finally` block. Expected-failure reports go in `tests/reports/negative-control/`.
This proves the suite can detect the original defect, rather than merely
confirming a successful run on one configured desktop.
