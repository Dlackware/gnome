config() {
  NEW="$1"
  OLD="$(dirname $NEW)/$(basename $NEW .new)"
  # If there's no config file by that name, mv it over:
  if [ ! -r $OLD ]; then
    mv $NEW $OLD
  elif [ "$(cat $OLD | md5sum)" = "$(cat $NEW | md5sum)" ]; then # toss the redundant copy
    rm $NEW
  fi
  # Otherwise, we leave the .new copy for the admin to consider...
}
config etc/polkit-1/rules.d/20-plugdev-group-mount-override.rules.new
config etc/polkit-1/rules.d/10-org.freedesktop.NetworkManager.rules.new

# Make sure the polkitd user and group exist:
if ! grep -q "^polkitd:" etc/passwd ; then
  echo "polkitd:x:87:87:PolicyKit daemon owner:/var/lib/polkit:/bin/false" >> etc/passwd
fi
if ! grep -q "^polkitd:" etc/group ; then
  echo "polkitd:x:87:" >> etc/group
fi

# Remove obsolete rules:
rm -f etc/polkit-1/localauthority/50-local.d/*.pkla{,.new}
rm -f etc/polkit-1/rules.d/*.pkla{,.new}

# Remove obsolete directory:
rmdir etc/polkit-1/localauthority/50-local.d 2> /dev/null
rmdir etc/polkit-1/localauthority 2> /dev/null

