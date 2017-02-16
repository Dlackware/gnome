chroot . rm -f /usr/share/icons/*/icon-theme.cache 1> /dev/null 2> /dev/null

chroot . /sbin/ldconfig 2> /dev/null
if [ -e usr/lib64/libX11.so.6 ] && [ -x usr/bin/gtk-query-immodules-3.0 ] ; then
  chroot . /usr/bin/update-gtk-immodules-3.0
fi

if [ -x usr/bin/glib-compile-schemas ] ;then
  chroot . /usr/bin/glib-compile-schemas --allow-any-name /usr/share/glib-2.0/schemas &> /dev/null
fi

chroot . systemctl enable update-gtk-immodules-3.service

if [ -x bin/systemctl ] ; then
  chroot . /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi


