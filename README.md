# Gnome 3 for Slackware Linux

<img src="screenshots/3.22.1.png" width="33%" alt="Gnome 3.22 on Slackware 14.2">
<img src="screenshots/3.22.2.png" width="33%" alt="Gnome 3.22 on Slackware 14.2">
<img src="screenshots/3.22.3.png" width="33%" alt="Gnome 3.22 on Slackware 14.2">
<img src="screenshots/3.22.4.png" width="33%" alt="Gnome 3.22 on Slackware 14.2">
<img src="screenshots/3.22.5.png" width="33%" alt="Gnome 3.22 on Slackware 14.2">

## About

Dlackware provides SlackBuild scripts for Gnome 3. The SlackBuilds found here
can be used seperatly, but are ment to work as a set on top of
[PAM](https://github.com/Dlackware/pam) and
[systemd](https://github.com/Dlackware/systemd).

It is a sources based project. We currently don't provide pre-built packages.
Since there are a lot of packages to build, we developed a small build
system which helps to build and install Gnome and its dependencies.

Our package set isn't the full Gnome distribution, but it isn't
minimalistic neither. If you miss some packages and you would like to
maintain them, fill free to create a pull request.


## Development

`master` branch is used for development of the next Dlackware version.

We support only the latest stable Slackware and one Gnome release per Slackware
version.

### Stable

Currently maintained release of Dlackware is Gnome 3.22 for Slackware 14.2.
To get this release use `3.22/14.2` branch.

### Current work

`master` is now updated for Gnome 3.36 on Slackware Current.

## Install

Full Slackware installation is required.

For Installation instruction please visit our
[INSTALL WIKI](https://github.com/Dlackware/gnome/wiki/Install).

### Finished, what now?

- Enable or disable services in /lib/systemd/system/ (dont forget gdm) (systemctl enable gdm.service)
- Set graphical-target (init 4) as default (systemctl set-default graphical.target)
- Or anything else you might forget

Reboot and have fun.
