#!/bin/sh
# Figure out our root directory
ROOTDIR=$(pwd)
unset CHROOT
if test "${ROOTDIR}" != "/"; then
  CHROOT="chroot ${ROOTDIR} "
  ROOTDIR="${ROOTDIR}/"
fi
if [ -x usr/bin/glib-compile-schemas ] ;then
  ${CHROOT} /usr/bin/glib-compile-schemas /usr/share/glib-2.0/schemas &> /dev/null
fi

if [ -x usr/bin/update-desktop-database ]; then
 ${CHROOT} /usr/bin/update-desktop-database 1> /dev/null 2> /dev/null
fi

if [ -x usr/bin/gtk-update-icon-cache ]; then
 ${CHROOT} /usr/bin/touch --no-create /usr/share/icons/hicolor > /dev/null 2>&1
 ${CHROOT} /usr/bin/gtk-update-icon-cache -q /usr/share/icons/hicolor > /dev/null 2>&1

fi
setcaps () {
if ${CHROOT} /sbin/setcap "\${1}" "\${3}" 2>/dev/null; then
 ${CHROOT} /bin/chmod "\${2}" "\${3}"
fi
}

setcaps 'cap_ipc_lock=ep' 'u-s' /usr/bin/gnome-keyring-daemon

