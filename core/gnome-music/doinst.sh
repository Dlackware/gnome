if [ -x /usr/bin/glib-compile-schemas ] ;then
  /usr/bin/glib-compile-schemas --allow-any-name /usr/share/glib-2.0/schemas &> /dev/null
fi
