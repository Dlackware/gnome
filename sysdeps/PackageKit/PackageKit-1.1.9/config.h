/* config.h.  Generated from config.h.in by configure.  */
/* config.h.in.  Generated from configure.ac by autoheader.  */

/* always defined to indicate that i18n is enabled */
#define ENABLE_NLS 1

/* Name of default gettext domain */
#define GETTEXT_PACKAGE "PackageKit"

/* minimum glib version */
#define GLIB_VERSION_MIN_REQUIRED GLIB_VERSION_2_44

/* Define to 1 if you have the `bind_textdomain_codeset' function. */
#define HAVE_BIND_TEXTDOMAIN_CODESET 1

/* Define to 1 if you have the Mac OS X function CFLocaleCopyCurrent in the
   CoreFoundation framework. */
/* #undef HAVE_CFLOCALECOPYCURRENT */

/* Define to 1 if you have the Mac OS X function CFPreferencesCopyAppValue in
   the CoreFoundation framework. */
/* #undef HAVE_CFPREFERENCESCOPYAPPVALUE */

/* Define to 1 if you have the `clearenv' function. */
#define HAVE_CLEARENV 1

/* define if the compiler supports basic C++11 syntax */
/* #undef HAVE_CXX11 */

/* define if the compiler supports basic C++14 syntax */
/* #undef HAVE_CXX14 */

/* Define to 1 if you have the `dcgettext' function. */
#define HAVE_DCGETTEXT 1

/* Set to true if apt is DDTP-enabled */
/* #undef HAVE_DDTP */

/* Define to 1 if you have the <dlfcn.h> header file. */
#define HAVE_DLFCN_H 1

/* Define to 1 if you have the <execinfo.h> header file. */
#define HAVE_EXECINFO_H 1

/* Define if the GNU gettext() function is already present or preinstalled. */
#define HAVE_GETTEXT 1

/* Define to 1 if you have the <inttypes.h> header file. */
#define HAVE_INTTYPES_H 1

/* Define if your <locale.h> file defines LC_MESSAGES. */
#define HAVE_LC_MESSAGES 1

/* Define to 1 if you have the `apt-inst' library (-lapt-inst). */
/* #undef HAVE_LIBAPT_INST */

/* Define to 1 if you have the `apt-pkg' library (-lapt-pkg). */
/* #undef HAVE_LIBAPT_PKG */

/* Define to 1 if you have the <locale.h> header file. */
#define HAVE_LOCALE_H 1

/* Define to 1 if you have the <memory.h> header file. */
#define HAVE_MEMORY_H 1

/* Define as 1 if you have polkit >= 0.114 */
/* #undef HAVE_POLKIT_0_114 */

/* Define to 1 if you have the `setpriority' function. */
#define HAVE_SETPRIORITY 1

/* Define to 1 if you have the <stdint.h> header file. */
#define HAVE_STDINT_H 1

/* Define to 1 if you have the <stdlib.h> header file. */
#define HAVE_STDLIB_H 1

/* Define to 1 if you have the <strings.h> header file. */
#define HAVE_STRINGS_H 1

/* Define to 1 if you have the <string.h> header file. */
#define HAVE_STRING_H 1

/* Build systemd code */
#define HAVE_SYSTEMD 1

/* Define to 1 if you have the <sys/stat.h> header file. */
#define HAVE_SYS_STAT_H 1

/* Define to 1 if you have the <sys/types.h> header file. */
#define HAVE_SYS_TYPES_H 1

/* Define to 1 if you have the <unistd.h> header file. */
#define HAVE_UNISTD_H 1

/* Define to the sub-directory where libtool stores uninstalled libraries. */
#define LT_OBJDIR ".libs/"

/* Name of package */
#define PACKAGE "PackageKit"

/* User for running the PackageKit daemon */
#define PACKAGEKIT_USER "root"

/* Define to the address where bug reports for this package should be sent. */
#define PACKAGE_BUGREPORT "richard@hughsie.com"

/* Define to the full name of this package. */
#define PACKAGE_NAME "PackageKit"

/* Define to the full name and version of this package. */
#define PACKAGE_STRING "PackageKit 1.1.9"

/* Define to the one symbol short name of this package. */
#define PACKAGE_TARNAME "PackageKit"

/* Define to the home page for this package. */
#define PACKAGE_URL "http://www.packagekit.org/"

/* Define to the version of this package. */
#define PACKAGE_VERSION "1.1.9"

/* Build local code */
/* #undef PK_BUILD_LOCAL */

/* Enable the daemon tests */
#define PK_ENABLE_DAEMON_TESTS 1

/* Define to 1 if you have the ANSI C header files. */
#define STDC_HEADERS 1

/* Version number of package */
#define VERSION "1.1.9"

/* define if libzypp returns package size in bytes */
/* #undef ZYPP_RETURN_BYTES */
