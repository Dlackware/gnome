function free_user_id {
  # Find a free user-ID >= 100 (should be < 1000 so it's not a normal user)
  local FREE_USER_ID=100
  while grep --quiet "^.*:.*:${FREE_USER_ID}:.*:.*:.*:" /etc/passwd; do
    let FREE_USER_ID++
  done
  echo ${FREE_USER_ID}
}

function free_group_id {
  # Find a free group-ID >= 120 (should be < 1000 so it's not a normal group)
  local FREE_GROUP_ID=120
  while grep --quiet "^.*:.*:${FREE_GROUP_ID}:" /etc/group; do
    let FREE_GROUP_ID++
  done
  echo ${FREE_GROUP_ID}
}

# Set up groups.
if ! grep --quiet '^gdm:' /etc/group ;then
    /usr/sbin/groupadd \
    -g $(free_group_id) \
    gdm 2> /dev/null
fi

# Set up user: add it if it doesn't exist, update it if it already does.
if OLD_ENTRY=$(grep --max-count=1 '^gdm:' /etc/passwd) \
  || OLD_ENTRY=$(grep --max-count=1 \
  ':/var/lib/gdm:[a-z/]*$' /etc/passwd)
then
  # Modify existing user
  OLD_USER=$(echo ${OLD_ENTRY} | cut --fields=1 --delimiter=':')
  USER_ID=$(echo ${OLD_ENTRY} | cut --fields=3 --delimiter=':')
  test ${USER_ID} -ge 1000 && USER_ID=$(free_user_id)
  if test "${OLD_USER}" = "gdm"; then
    echo -n "Updating unprivileged user " 1>&2
  else
    echo -ne "Changing unprivileged user \e[1m${OLD_USER}\e[0m to" 1>&2
  fi
      /usr/sbin/usermod \
      -d '/var/lib/gdm' \
      -u ${USER_ID} \
      -s /bin/false \
      -g gdm \
      ${OLD_USER}
else
  # Add new user
  echo -n "Creating unprivileged user" 1>&2
    /usr/sbin/useradd \
    -c 'GDM Daemon Owner' \
    -u $(free_user_id) \
    -g gdm \
    -s /bin/false \
    -d '/var/lib/gdm' \
    gdm 2> /dev/null
fi

usermod -a -G audio gdm &&
usermod -a -G video gdm


if [ ! -d var/lib/gdm ]; then
        mkdir -p /var/lib/gdm
fi

chroot . chown -R gdm:gdm /var/lib/gdm /var/cache/gdm /var/log/gdm
chroot . chmod 0755 /var/lib/gdm /var/cache/gdm /var/log/gdm

chroot . /usr/bin/dconf update

chroot . chown -R root:gdm /var/run/gdm
chroot . chmod 1777 /var/run/gdm

if [ -x bin/systemctl ] ; then
  /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi
