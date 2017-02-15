config() {
  NEW="$1"
  OLD="$(dirname $NEW)/$(basename $NEW .new)"
  # If there's no config file by that name, mv it over:
  if [ ! -r $OLD ]; then
    mv $NEW $OLD
  elif [ "$(cat $OLD | md5sum)" = "$(cat $NEW | md5sum)" ]; then
    # toss the redundant copy
    rm $NEW
  fi
  # Otherwise, we leave the .new copy for the admin to consider...
}

config etc/wpa_supplicant.conf.new
config etc/logrotate.d/wpa_supplicant.new

if [ -x usr/bin/update-desktop-database ]; then
  chroot . /usr/bin/update-desktop-database /usr/share/applications >/dev/null 2>&1
fi
if [ -x usr/bin/gtk-update-icon-cache ]; then
  chroot . /usr/bin/touch --no-create /usr/share/icons/hicolor >/dev/null 2>&1
  chroot . /usr/bin/gtk-update-icon-cache /usr/share/icons/hicolor >/dev/null 2>&1
fi

if [ -x bin/systemctl ] ; then
  chroot . /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi
