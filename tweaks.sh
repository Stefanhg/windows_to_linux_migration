#!/bin/sh
# Run as the desktop user, inside their Cinnamon session.
set -eu
# Flatpak IDE terminals see the SDK's programs and settings, not the desktop's.
if [ -f /.flatpak-info ]; then
    if ! command -v flatpak-spawn >/dev/null 2>&1; then
        echo 'Run sh tweaks.sh from the Linux Mint Terminal outside Flatpak.' >&2
        exit 1
    fi
    exec flatpak-spawn --host sh "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/tweaks.sh" "$@"
fi
exec python3 "$(dirname "$0")/tweaks.py" "$@"
