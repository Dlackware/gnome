#!/bin/sh
# Figure out our root directory
ROOTDIR=$(pwd)
unset CHROOT
if test "${ROOTDIR}" != "/"; then
  CHROOT="chroot ${ROOTDIR} "
  ROOTDIR="${ROOTDIR}/"
fi


if [ -x /usr/bin/update-mime-database ]; then
  /usr/bin/update-mime-database /usr/share/mime 1>/dev/null 2>/dev/null
  cat /etc/passwd | while read passwdline ; do
    homedir=$(echo $passwdline | cut -f 6 -d :)
    if [ -d $homedir/.local/share/mime ]; then
      username=$(echo $passwdline | cut -f 1 -d :)
      # Sorry about the long command line, alienBOB  ;-)
      su $username -c "/usr/bin/update-mime-database $homedir/.local/share/mime 1>/dev/null 2>/dev/null" 2> /dev/null
    fi
  done
  # This is just "cleanup" in case something might be missed in /home/*/
  for homemimedir in /home/*/.local/share/mime ; do
    if [ -d $homemimedir ]; then
      username=$(echo $homemimedir | cut -f 3 -d /)
      su $username -c "/usr/bin/update-mime-database $homemimedir 1>/dev/null 2>/dev/null" 2> /dev/null
    fi
  done
fi

if [ -x bin/systemctl ]; then
   ${CHROOT} . /bin/systemctl --system daemon-reload >/dev/null 2>&1
   ${CHROOT} . /bin/systemctl enable update-mime-database.service >/dev/null 2>&1
fi
