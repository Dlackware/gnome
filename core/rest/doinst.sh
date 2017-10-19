if [ -x usr/sbin/update-ca-certificates ]; then
  chroot . /usr/sbin/update-ca-certificates
fi
