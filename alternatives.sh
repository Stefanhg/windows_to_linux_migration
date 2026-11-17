#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -f /.flatpak-info ]; then
    exec flatpak-spawn --host sh "$project_dir/alternatives.sh" "$@"
fi
exec python3 "$project_dir/alternatives.py" "$@"
