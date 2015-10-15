function free_user_id {
  # Find a free user-ID >= 100 (should be < 1000 so it's not a normal user)
  local FREE_USER_ID=100
  while grep --quiet "^.*:.*:${FREE_USER_ID}:.*:.*:.*:" etc/passwd; do
    let FREE_USER_ID++
  done
  echo ${FREE_USER_ID}
}
function free_group_id {
  # Find a free group-ID >= 120 (should be < 1000 so it's not a normal group)
  local FREE_GROUP_ID=100
  while grep --quiet "^.*:.*:${FREE_GROUP_ID}:" etc/group; do
    let FREE_GROUP_ID++
  done
  echo ${FREE_GROUP_ID}
}

# Figure out our root directory
ROOTDIR=$(pwd)
unset CHROOT
if test "${ROOTDIR}" != "/"; then
 CHROOT="chroot ${ROOTDIR} "
  ROOTDIR="${ROOTDIR}/"
fi

# Set up groups.
if ! grep --quiet '^colord:' etc/group ;then
  ${CHROOT} /usr/sbin/groupadd \
    -g $(free_group_id) \
    colord 2> /dev/null
fi

# Set up user: add it if it doesn't exist, update it if it already does.
if OLD_ENTRY=$(grep --max-count=1 '^colord:' etc/passwd) \
  || OLD_ENTRY=$(grep --max-count=1 \
  ':/var/lib/colord:[a-z/]*$' etc/passwd)
then
  # Modify existing user
  OLD_USER=$(echo ${OLD_ENTRY} | cut --fields=1 --delimiter=':')
  USER_ID=$(echo ${OLD_ENTRY} | cut --fields=3 --delimiter=':')
  test ${USER_ID} -ge 1000 && USER_ID=$(free_user_id)
  if test "${OLD_USER}" = "colord"; then
    echo -n "Updating unprivileged user " 1>&2
  else
    echo -ne "Changing unprivileged user \e[1m${OLD_USER}\e[0m to " 1>&2
  fi
  ${CHROOT} /usr/sbin/usermod \
      -d '/var/lib/colord' \
      -u ${USER_ID} \
      -s /bin/false \
      -g colord \
      ${OLD_USER}
else
  # Add new user
  echo -n "Creating unprivileged user " 1>&2
  ${CHROOT} /usr/sbin/useradd \
    -c 'User for colord' \
    -u $(free_user_id) \
    -g colord \
    -s /bin/false \
    -d '/var/lib/colord' \
    colord 2> /dev/null
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
## List of conf files to check.  The conf files in your package should end in .new
config var/lib/colord/mapping.db.new
config var/lib/colord/storage.db.new
rm -f var/lib/colord/mapping.db.new
rm -f var/lib/colord/storage.db.new

# Fix permissions
${CHROOT} /bin/chown colord.colord /var/lib/colord
${CHROOT} /bin/chown colord.colord /var/lib/colord/icc
${CHROOT} /bin/chown colord.colord /var/lib/colord/mapping.db
${CHROOT} /bin/chown colord.colord /var/lib/colord/storage.db

if [ -x bin/systemctl ] ; then
  ${CHROOT} /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi
