chroot . /bin/killall /usr/libexec/dconf-service &> /dev/null

chroot . /sbin/ldconfig 2> /dev/null

if [ -x /usr/bin/gio-querymodules ] ; then
  chroot . /usr/bin/gio-querymodules /usr/lib64/gio/modules &> /dev/null
fi

if [ -x /usr/bin/glib-compile-schemas ] ;then
  chroot . /usr/bin/glib-compile-schemas /usr/share/glib-2.0/schemas &> /dev/null
fi

if [ -x /usr/bin/update-desktop-database ]; then
  chroot . /usr/bin/update-desktop-database 1> /dev/null 2> /dev/null
fi

if [ -x /usr/bin/gtk-update-icon-cache ]; then
  chroot . /usr/bin/touch --no-create /usr/share/icons/hicolor > /dev/null 2>&1
  chroot . /usr/bin/gtk-update-icon-cache -q /usr/share/icons/hicolor > /dev/null 2>&1
fi
