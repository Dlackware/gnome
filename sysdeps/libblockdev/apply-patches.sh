
set -e -o pipefail

SBO_PATCHDIR=${CWD}/patches

# patch -p0 -E --backup --verbose -i ${SB_PATCHDIR}/${NAME}.patch
patch -p0 -E --backup --verbose -i ${SBO_PATCHDIR}/udisks-2.x-ntfs-3g.patch
#patch -p0 -E --backup --verbose -i ${SBO_PATCHDIR}/udisks2-2.1.2-systemd209.patch

# Set to YES if autogen is needed
SBO_AUTOGEN=NO

set +e +o pipefail
