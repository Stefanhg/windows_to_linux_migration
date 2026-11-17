#!/bin/sh
set -eu

if [ "$(id -u)" -eq 0 ]; then
    printf 'Run the font setup as your desktop user.\n' >&2
    exit 1
fi

has_inter_regular() {
    command -v fc-match >/dev/null 2>&1 &&
        [ "$(fc-match -f '%{family}|%{style}' Inter)" = 'Inter|Regular' ]
}

if ! has_inter_regular; then
    sudo apt-get update
    sudo apt-get install -y fontconfig fonts-inter
fi

if ! has_inter_regular; then
    printf 'Fontconfig could not resolve Inter Regular.\n' >&2
    exit 1
fi

gsettings set org.cinnamon.desktop.interface font-name 'Inter 11'
gsettings set org.nemo.desktop font 'Inter 11'
gsettings set org.gnome.desktop.interface document-font-name 'Inter 11'
