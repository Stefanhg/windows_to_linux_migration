#!/bin/sh
# Run against an already-configured, disposable Mint Cinnamon X11 desktop.
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ -f /.flatpak-info ]; then
    exec flatpak-spawn --host sh "$project_dir/tests/desktop.sh" "$@"
fi
cd "$project_dir"
export PYTHONPATH="$project_dir/tests/.deps${PYTHONPATH:+:$PYTHONPATH}"
if [ "${1:-}" = '--check-regression' ]; then
    shift
    exec python3 tests/check_regression.py "$@"
fi
exec python3 -m behave tests/features --junit --junit-directory tests/reports "$@"
