# Gnome 3 Desktop for Slackware Linux
-----

[VERSIONS]
Gnome-3.16 -- Slackware-14.2 <-- build against current okt. 2015) -- beta status

[NOTES]
The SlackBuilds found here can be used seperatly,
but are ment to work as a set on top of https://github.com/Dlackware/systemd

[INSTALL]
Requirements:
- Full Install of Slackware
- All the packages from https://github.com/Dlackware/systemd that are required

In the directory base/ you can find the file compile-order
Build and install all the files on that list

Alternative method:
We have a build system that makes everything easier,
the build system reads the compile-order file and builds and installs everything on that list.
It can also download the latest scripts install from compiled packages.
The Installer can be found here https://github.com/Dlackware/dlackware

Finished, what now ?
- enable or disable services in /lib/systemd/system/ (dont forget gdm)
- set graphical-target (init 4) as default
- or anything else you might forget
Reboot and have fun.
