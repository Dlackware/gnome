chroot . /sbin/ldconfig 2> /dev/null
if [ -e /usr/lib64/libX11.so.6 ] && [ -x /usr/bin/gtk-query-immodules-3.0 ] ; then
  chroot . /usr/bin/update-gtk-immodules-3.0
fi

if [ -x /usr/bin/gtk-query-immodules-2.0 ] ; then
  chroot . /usr/bin/update-gtk-immodules-2.0
fi

if [ -x /usr/bin/update-gdk-pixbuf-loaders ] ; then
  chroot . /usr/bin/update-gdk-pixbuf-loaders
fi

if [ -x /usr/bin/glib-compile-schemas ] ; then
  chroot . /usr/bin/glib-compile-schemas --allow-any-name /usr/share/glib-2.0/schemas &> /dev/null
fi

if [ -x /usr/bin/update-mime-database ]; then
  /usr/bin/update-mime-database usr/share/mime >/dev/null 2>&1
fi

if [ -x /bin/systemctl ] ; then
  chroot . /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi

