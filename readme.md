# Windows-to-Linux migration project

This project aims to make Linux Mint 22 Cinnamon feel familiar to Windows users, with a productive desktop and as little configuration as possible.

## Scripts

Run the scripts from the repository root as your regular user in a Cinnamon desktop session. Install Flameshot before applying the tweaks. The Task Manager setup requires Flatpak with Flathub configured.

| Script | What it does |
| --- | --- |
| [install_all.sh](install_all.sh) | Runs the desktop tweaks and the Task Manager setup. |
| [tweaks.sh](tweaks.sh) | Applies the Cinnamon panel, window, and screenshot tweaks. |
| [alternatives.sh](alternatives.sh) | Installs Mission Center if needed and adds a Task Manager launcher and keyboard shortcut. |

## Windows apps and Linux alternatives

Mission Center is set up by the Task Manager script. Flameshot is a prerequisite for the screenshot shortcut, and Remmina can be installed separately.

| Windows app | Linux alternative | Install manually |
| --- | --- | --- |
| Task Manager | Mission Center | `flatpak install flathub io.missioncenter.MissionCenter` |
| Remote Desktop | Remmina | `flatpak install flathub org.remmina.Remmina` |
| Snipping Tool | Flameshot | `sudo apt install flameshot` |

### Optional apps

| Windows app | Linux alternative | Install | Notes |
| --- | --- | --- | --- |
| PuTTY | PuTTY | `sudo apt install putty` | I recall having some reliability issues with it. |
| Notepad++ | Notepad Next | `flatpak install flathub com.github.dail8859.NotepadNext` | |
| Microsoft Office | ONLYOFFICE | `flatpak install flathub org.onlyoffice.desktopeditors` | |
| VS Code | VS Code | `flatpak install flathub com.visualstudio.code` | |
| Media player | VLC | `flatpak install flathub org.videolan.VLC` | |

## Desktop tweaks

- Add a taskbar on the second monitor with a mirrored task list, pinned launchers, and supported applets such as the clock.
- Increase taskbar height from 40 to 60 logical pixels and scale up panel icons.
- Maximize a window when you drag it to the top edge of the screen.
- Change default font to inter regular, this was due to me finding default font hard to read.

### Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| <kbd>Super</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> | Open Flameshot for a region capture. The default <kbd>Print Screen</kbd> shortcut is also available. |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Esc</kbd> | Open Mission Center (Task Manager). |

### To do

- Explore adding “Open in…” actions for editors such as VS Code and Notepad++. See the [Dolphin service menus in Michael Matta's migration project](https://github.com/Michael-Matta1/win2linux-migration).

## Why Mint?

I use Ubuntu at work and have tried Kali, Debian, Ubuntu releases from 22 to 26, and Zorin, which I used on my school laptop for a year. Mint 22 Cinnamon felt the most like home straight away.

For me, an operating system is a productivity tool. I want a familiar desktop that feels comfortable out of the box and needs only a few adjustments.

## Gaming

I've found Lutris useful for installing Windows games. You can share a YAML installer script so others can automate the same setup.

## Dual boot for games that need Windows

Some games still need Windows. I experimented with a dual-boot setup on Ubuntu that let me hibernate Linux, reboot into Windows, and resume Linux later. I added a menu entry on Linux and used a desktop batch file on Windows as part of the return workflow. See the [dual-boot hibernation project](https://github.com/TheSalaty/dual-boot-hibernation) for the approach.

## More migration resources

- [Linux Base Camp app directory](https://linuxbasecamp.com/apps) and [AlternativeTo](https://alternativeto.net/) list software alternatives.
- [Samillion's Windows-to-Linux notes](https://github.com/Samillion/Windows-to-Linux) document migration requirements and challenges.
- [Michael Matta's Windows-to-Linux migration project](https://github.com/Michael-Matta1/win2linux-migration) takes an approach similar to this one.

## Development

See the [development notes](development.md) for the testing strategy and [desktop acceptance tests](tests/README.md) for setup and commands.
