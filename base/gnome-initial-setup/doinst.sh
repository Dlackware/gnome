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
if ! grep --quiet '^gnome-initial-setup:' etc/group ;then
  ${CHROOT} /usr/sbin/groupadd \
    -g $(free_group_id) \
    gnome-initial-setup 2> /dev/null
fi

# Set up user: add it if it doesn't exist, update it if it already does.
if OLD_ENTRY=$(grep --max-count=1 '^gnome-initial-setup:' etc/passwd) \
  || OLD_ENTRY=$(grep --max-count=1 \
  ':/var/lib/gnome-initial-setup:[a-z/]*$' etc/passwd)
then
  # Modify existing user
  OLD_USER=$(echo ${OLD_ENTRY} | cut --fields=1 --delimiter=':')
  USER_ID=$(echo ${OLD_ENTRY} | cut --fields=3 --delimiter=':')
  test ${USER_ID} -ge 1000 && USER_ID=$(free_user_id)
  if test "${OLD_USER}" = "gnome-initial-setup"; then
    echo -n "Updating unprivileged user " 1>&2
  else
    echo -ne "Changing unprivileged user \e[1m${OLD_USER}\e[0m to " 1>&2
  fi
  ${CHROOT} /usr/sbin/usermod \
      -d '/var/lib/gnome-initial-setup' \
      -u ${USER_ID} \
      -s /sbin/nologin \
      -g gnome-initial-setup \
      ${OLD_USER}
else
  # Add new user
  echo -n "Creating unprivileged user " 1>&2
  ${CHROOT} /usr/sbin/useradd \
    -c 'User for gnome-initial-setup' \
    -u $(free_user_id) \
    -g gnome-initial-setup \
    -s /sbin/nologin \
    -d '/var/lib/gnome-initial-setup' \
    gnome-initial-setup 2> /dev/null
fi
