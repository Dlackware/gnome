systemctl enable update-gdk-pixbuf-loaders.service

if [ -x bin/systemctl ] ; then
  /bin/systemctl --system daemon-reload >/dev/null 2>&1
fi

