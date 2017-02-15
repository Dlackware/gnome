# Figure out our root directory
ROOTDIR=$(pwd)
unset CHROOT
if test "${ROOTDIR}" != "/"; then
  CHROOT="chroot ${ROOTDIR} "
  ROOTDIR="${ROOTDIR}/"
fi

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

preserve_perms() {
  NEW="$1"
  OLD="$(dirname ${NEW})/$(basename ${NEW} .new)"
  if [ -e ${OLD} ]; then
    cp -a ${OLD} ${NEW}.incoming
    cat ${NEW} > ${NEW}.incoming
    mv ${NEW}.incoming ${NEW}
  fi
  mv ${NEW} ${OLD}
}

if [ -e etc/HOSTNAME ]; then
  sed -i "s,yourhostname,$(cat etc/HOSTNAME | cut -f1 -d .)," \
    etc/NetworkManager/NetworkManager.conf.new
fi

config etc/NetworkManager/NetworkManager.conf.new

# Do not enable NetworkManager or start
# If you want, disable systemd-networkd
#if [ -x bin/systemctl ] ; then
# /bin/systemctl enable NetworkManager >/dev/null 2>&1
#fi

if [ -x bin/systemctl ] ; then
 ${CHROOT} /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi

