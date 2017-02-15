
set -e -o pipefail

# patch -p0 -E --backup --verbose -i ${CWD/${NAME}.patch
#patch -p1 -E --backup --verbose -i ${CWD}/avahi-0.6.17-nonetdevneeded.diff
#patch -p1 -E --backup --verbose -i ${CWD}/reserve-space-for-data-record.patch
#patch -p1 -E --backup --verbose -i ${CWD}/hostname-machineid.patch
#patch -p1 -E --backup --verbose -i ${CWD}/avahi-privacy.patch
#patch -p1 -E --backup --verbose -i ${CWD}/gtk-box-new.patch
#patch -p1 -E --backup --verbose -i ${CWD}/avahi-0.6.31-no-deprecations.patch

set +e +o pipefail
