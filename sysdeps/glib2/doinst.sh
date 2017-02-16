# Handle the incoming configuration files:
config() {
  for infile in $1; do
    NEW="$infile"
    OLD="`dirname $NEW`/`basename $NEW .new`"
    # If there's no config file by that name, mv it over:
    if [ ! -r $OLD ]; then
      mv $NEW $OLD
    elif [ "`cat $OLD | md5sum`" = "`cat $NEW | md5sum`" ]; then
      # toss the redundant copy
      rm $NEW
    fi
    # Otherwise, we leave the .new copy for the admin to consider...
  done
}

# Prepare the new configuration files
for file in etc/profile.d/libglib2.csh.new etc/profile.d/libglib2.sh.new ; do
  if test -e $(dirname $file)/$(basename $file .new) ; then
    if [ ! -x $(dirname $file)/$(basename $file .new) ]; then
      chmod 644 $file
     else
      chmod 755 $file
    fi
  fi
  config $file
done

chroot . /sbin/ldconfig 2> /dev/null
if [ -x usr/bin/update-gio-modules ] ; then
chroot . /usr/bin/update-gio-modules &> /dev/null
fi

if [ -x usr/bin/glib-compile-schemas ] ;then
chroot . /usr/bin/glib-compile-schemas --allow-any-name /usr/share/glib-2.0/schemas &> /dev/null
fi

chroot . systemctl enable glib-compile-schemas.service
chroot . systemctl enable update-gio-modules.service

if [ -x bin/systemctl ] ; then
chroot . /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi

