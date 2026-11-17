
## Windows-to-Linux migration Project

Target OS: Linux Mint 22 Cinnamon
Goal: Deliver a familiar, productive Windows-like desktop experience with minimal configuration.

Project Philosophy

We are working on a project to provide the best possible experience when migrating from Windows to Linux.
Our chosen operating system is Linux Mint 22 Cinnamon.
Why Mint? Because its out-of-the-box experience feels familiar. See `Why Mint?` for the full explanation.

## Scripts overview

| Name              | Function                                                               |
|-------------------|------------------------------------------------------------------------|
| install_all.sh    | Deploys all recommendations from this guide                            |
| tweaks.sh         | Applies all tweaks suggested here                                      |
| alternatives.sh   | Deploys the alternative application e.g. Task Manager alternative      |

## Classic Applications & Linux Alternatives

Alternatives that directly gets mapped to equvilient when deployed
They are preinstalled by default

| Windows App     | Linux Alternative | Install                                                                  |
|-----------------|-------------------|--------------------------------------------------------------------------|
| Task Manager    | Mission Monitor   | `flatpak install flathub io.missioncenter.MissionCenter`                 |
| Remote Desktop  | Remmina           | `flatpak install flathub org.remmina.Remmina`                            |
| Snipping Tool   | Flameshot         | `sudo apt install flameshot`                                             |

Alternatives that can be installed

| Windows App      | Linux Alternative | Install | Notes |
|------------------|---------------|-----------------------------------------------------------|--------------------------------------------------------|
| PuTTY            | Putty         | `sudo apt install putty`                                  | Note I remember this might not be completely reliable! |
| Notepad++        | Notepad Next  | `flatpak install flathub com.github.dail8859.NotepadNext` | |
| Microsoft Office | OnlyOffice    | `flatpak install flathub org.onlyoffice.desktopeditors` |   |
| VS Code          | VS Code       | `flatpak install flathub com.visualstudio.code` | |
| Media player     | VLC           | `flatpak install flathub org.videolan.VLC` | |


## Tweaks

We attempt to avoid tweaking behavior as much as possible to let user feel comfortable in their own way, but tweak where it is needed.

- Make taskbar appear on second screen, including it's icons and time.
- Increase taskbar and icon size 150%, as it felt too small
- Make moving window to top of screen full size instead of half size
- Duplicate the taskbar on each screen(instead of just containing apps)'

# Shortuts
- Mapped Windows(super) + Shift + S to flameshot as alternative, keeping default too (default Printscreen)
- Mapped CTRL + Shift + ESC to opening Task Manager(Mission Monitor)

Todo:;
- Open IN XXXX e.g. Vs Code, notepad+ or other. Look into Dolphin Service Menus https://github.com/Michael-Matta1/win2linux-migration


## Development
Read `development.md` (note make clickable)

## Why mint?

I have through many years tested many OS'es and Linux Mint out of the box had an amazing experince.
I daily drive Ubuntu at work, tried:
- Kali,
- Debian,
- Ubuntu 22-26,
- Zorin(was daily driver for a year on school laptop)

While all was decent to use, nothing have felt like home like Mint 22.

I am very focused on out-of-box experince with no tweaks needed as an OS for me is my productivity tool, i don't want to tweak it to to make it work.
And I like familiarity so this got me close to Windows experince.

## Gaming

I found `Lutris` to be amazing for deploying **Windows** games. You create a YAML for others to use, and then it can be used to automatically deployment.


## Last resort dual boot.

While we do seek game compatability to be 100% functional, of course not all are.
In this case we can apply hybrid sleep to Linux / Windows.
This allows for hybrid sleeping, reboot machine and then go back into Windows.
I fiddled with it on Ubuntu and got a pretty decent result with it.
I added a menu entry to enter Windows from Linux and on Windows a .bat file on desktop
Sadly Windows does not allow directly booting into Linux, so i had to do some tweaking there
to make it work.
Read more about the approach: https://github.com/TheSalaty/dual-boot-hibernation


## Windows To Linux Alternatives lists

Various websites that contains alternative lists

https://linuxbasecamp.com/apps
https://alternativeto.net/

## Other migration information

While researching i also found other's migration notes

| Link | Notes |
| https://github.com/Samillion/Windows-to-Linux | Interesting process documenting his struggles and requirements |
| https://github.com/Michael-Matta1/win2linux-migration | Closely resembles what I have been working on here!  |

