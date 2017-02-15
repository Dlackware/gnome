if [ -x /usr/bin/gio-querymodules ]; then
  chroot . /usr/bin/gio-querymodules @LIBDIR@/gio/modules/ >/dev/null 2>&1
fi

