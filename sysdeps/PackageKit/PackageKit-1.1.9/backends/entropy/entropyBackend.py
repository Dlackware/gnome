#!/usr/bin/python2
# -*- coding: utf-8 -*-
#
#
# Copyright (C) 2009 Mounir Lamouri (volkmar) <mounir.lamouri@gmail.com>
# Copyright (C) 2010 Fabio Erculiani (lxnay) <lxnay@sabayon.org>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import os
import sys
import signal
import time
import traceback
import threading

from packagekit.enums import *

from packagekit.backend import PackageKitBaseBackend, get_package_id, \
    split_package_id
from packagekit.package import PackagekitPackage

sys.path.insert(0, '/usr/lib/entropy/libraries')
sys.path.insert(0, '/usr/lib/entropy/lib')

from entropy.output import decolorize
from entropy.i18n import _, _LOCALE
from entropy.const import etpConst, const_convert_to_rawstring, \
    const_convert_to_unicode, const_get_stringtype
from entropy.client.interfaces import Client
from entropy.client.interfaces.db import InstalledPackagesRepository
from entropy.core.settings.base import SystemSettings
from entropy.misc import LogFile
from entropy.cache import EntropyCacher
from entropy.exceptions import SystemDatabaseError, DependenciesNotFound, \
    DependenciesCollision, EntropyPackageException
from entropy.db.exceptions import Error as EntropyRepositoryError
from entropy.exceptions import DependenciesNotRemovable
from entropy.fetchers import UrlFetcher
from entropy.services.client import WebService
from entropy.locks import EntropyResourcesLock

import entropy.tools
import entropy.dep

PK_DEBUG = False


def sharedreslock(method):
    """
    Entropy Resources Lock decorator for shared mode.
    """
    def wrapped(*args, **kwargs):
        lock = EntropyResourcesLock(output=PackageKitEntropyClient)
        with lock.shared():
            return method(*args, **kwargs)

    return wrapped


def exclusivereslock(method):
    """
    Entropy Resources Lock decorator for exclusive mode.
    """
    def wrapped(*args, **kwargs):
        lock = EntropyResourcesLock(output=PackageKitEntropyClient)
        with lock.exclusive():
            return method(*args, **kwargs)

    return wrapped


def sharedinstlock(method):
    """
    Decorator that acquires the Installed Packages Repository lock in
    shared mode and calls the wrapped function with an extra argument
    (the Installed Packages Repository object instance).
    """

    def wrapped(self, *args, **kwargs):
        inst_repo = self._entropy.installed_repository()
        with inst_repo.shared():
            return method(self, *args, **kwargs)

    return wrapped


def exclusiveinstlock(method):
    """
    Decorator that acquires the Installed Packages Repository lock in
    exclusive mode and calls the wrapped function with an extra
    argument (the Installed Packages Repository object instance).
    """

    def wrapped(self, *args, **kwargs):
        inst_repo = self._entropy.installed_repository()
        with inst_repo.exclusive():
            return method(self, *args, **kwargs)

    return wrapped


class PackageKitEntropyMixin(object):

    INST_PKGS_REPO_ID = "installed"

    """
    Entropy relaxed code can be found in this Mixin class.
    The aim is to separate PackageKit code and reimplemented methods from
    Entropy-only protected methods.
    """

    @staticmethod
    def get_percentage(count, max_count):
        """
        Prepare percentage value used to feed self.percentage()
        """
        percent = int((float(count) / max_count) * 100)
        if percent > 100:
            return 100
        return percent

    def _log_message(self, source, *args):
        """
        Write log message to Entropy PackageKit log file.
        """
        if PK_DEBUG:
            my_args = []
            for arg in args:
                if not isinstance(arg, const_get_stringtype()):
                    my_args.append(repr(arg))
                else:
                    my_args.append(arg)

            self._entropy_log.write("%s: %s" % (source,
                                                ' '.join([const_convert_to_unicode(x) for x in my_args]),)
                                    )

    def _encode_string_list(self, values):
        # values is a list of unencoded strings, we need UTF-8 strings here
        return [const_convert_to_unicode(x) for x in values]

    def _is_repository_enabled(self, repo_name):
        """
        Return whether given repository identifier is available and enabled.
        """
        repo_data = self._settings['repositories']
        return repo_name in repo_data['available']

    def _etp_to_id(self, pkg_match):
        """
        Transform an Entropy package match (pkg_id, EntropyRepository) into
        PackageKit id.
        @param pkg_match: tuple composed by package identifier and its parent
            EntropyRepository instance
        @type pkg_match: tuple
        @return: PackageKit package id
        @rtype: string
        """
        pkg_id, c_repo = pkg_match

        pkg_key, pkg_slot, pkg_ver, pkg_tag, pkg_rev, atom = \
            c_repo.getStrictData(pkg_id)

        pkg_ver += "%s%s" % (etpConst['entropyslotprefix'], pkg_slot,)
        if pkg_tag:
            pkg_ver += "%s%s" % (etpConst['entropytagprefix'], pkg_tag)

        cur_arch = etpConst['currentarch']
        repo_name = self._get_repo_name(c_repo)
        if repo_name is None:
            self.error(ERROR_PACKAGE_ID_INVALID,
                       "Invalid metadata passed")

        # if installed, repo should be 'installed', packagekit rule
        cl_repo_name = etpConst.get(
            'clientdbid',  # forward compatibility
            getattr(InstalledPackagesRepository, "NAME", None))
        if repo_name == cl_repo_name:
            repo_name = "installed"

        # openoffice-clipart;2.6.22;ppc64;fedora
        return get_package_id(pkg_key, pkg_ver, cur_arch, repo_name)

    def _id_to_etp(self, pkit_id):
        """
        Transform a PackageKit package id into Entropy package match.

        @param pkit_id: PackageKit package id
        @type pkit_id: string
        @return: tuple composed by package identifier and its parent
            EntropyRepository instance
        @rtype: tuple
        """
        split_data = split_package_id(pkit_id)
        if len(split_data) < 4:
            self.error(ERROR_PACKAGE_ID_INVALID,
                       "The package id %s does not contain 4 fields" % pkit_id)
            return
        pkg_key, pkg_ver, cur_arch, repo_name = split_data

        self._log_message(__name__,
                          "_id_to_etp: extracted: %s | %s | %s | %s" % (
                              pkg_key, pkg_ver, cur_arch, repo_name,))
        pkg_ver, pkg_slot = pkg_ver.rsplit(":", 1)

        if repo_name == "installed":
            c_repo = self._entropy.installed_repository()
        else:
            c_repo = self._entropy.open_repository(repo_name)

        atom = pkg_key + "-" + pkg_ver + etpConst['entropyslotprefix'] + \
            pkg_slot
        pkg_id, pkg_rc = c_repo.atomMatch(atom)
        if pkg_rc != 0:
            self.error(ERROR_PACKAGE_ID_INVALID,
                       "Package not found in repository")
            return

        return pkg_id, c_repo

    def _get_pk_group(self, category):
        """
        Return PackageKit group belonging to given Entropy package category.
        """
        group_data = [key for key, data in
                      self._entropy.get_package_groups().items()
                      if category in data['categories']]
        try:
            generic_group_name = group_data.pop(0)
        except IndexError:
            return GROUP_UNKNOWN

        return PackageKitEntropyBackend.GROUP_MAP[generic_group_name]

    def _get_entropy_group(self, pk_group):
        """
        Given a PackageKit group identifier, return Entropy packages group.
        """
        group_map = PackageKitEntropyBackend.GROUP_MAP
        # reverse dict
        group_map_reverse = dict((y, x) for x, y in group_map.items())
        return group_map_reverse.get(pk_group, 'unknown')

    def _get_all_repos(self):
        """
        Return a list of tuples containing EntropyRepository instance and
        repository identifier for every available repository, including
        installed packages one.
        """
        inst_pkgs_repo_id = PackageKitEntropyMixin.INST_PKGS_REPO_ID
        repo_ids = self._entropy.repositories() + [inst_pkgs_repo_id]
        repos = []
        for repo in repo_ids:
            if repo == inst_pkgs_repo_id:
                repo_db = self._entropy.installed_repository()
            else:
                repo_db = self._entropy.open_repository(repo)
            repos.append((repo_db, repo,))
        return repos

    def _get_pkg_size(self, pkg_match):
        """
        Return package size for both installed and available packages.
        For available packages, the download size is returned, for installed
        packages, the on-disk size is returned instead.
        """
        pkg_id, c_repo = pkg_match
        size = 0
        if c_repo is self._entropy.installed_repository():
            size += c_repo.retrieveOnDiskSize(pkg_id)
        else:
            size += c_repo.retrieveSize(pkg_id)

        supports_extra_download = hasattr(c_repo, "retrieveExtraDownload")
        if not supports_extra_download:
            return size

        cl_id = etpConst['system_settings_plugins_ids']['client_plugin']
        debug = self._settings[cl_id]['misc']['splitdebug']
        extra_downloads = c_repo.retrieveExtraDownload(pkg_id)
        for extra_download in extra_downloads:
            if (not debug) and (extra_download['type'] == "debug") and \
                    (c_repo is not self._entropy.installed_repository()):
                continue
            if c_repo is self._entropy.installed_repository():
                size += extra_download['disksize']
            else:
                size += extra_download['size']
        return size

    def _pk_feed_sorted_pkgs(self, pkgs):
        """
        Given an unsorted list of tuples composed by repository identifier and
        EntropyRepository instance, feed PackageKit output by calling
        self._package()
        """
        lambda_sort = lambda x: x[2].retrieveAtom(x[1])

        for repo, pkg_id, c_repo, pkg_type in sorted(pkgs, key=lambda_sort):
            self._package((pkg_id, c_repo), info=pkg_type)

    def _pk_filter_pkgs(self, pkgs, filters):
        """
        Filter pkgs list given PackageKit filters.
        """
        inst_pkgs_repo_id = PackageKitEntropyMixin.INST_PKGS_REPO_ID

        if FILTER_INSTALLED in filters:
            pkgs = set([x for x in pkgs if x[0] == inst_pkgs_repo_id])
        elif FILTER_NOT_INSTALLED in filters:
            pkgs = set([x for x in pkgs if x[0] != inst_pkgs_repo_id])
        if FILTER_FREE in filters:
            pkgs = set([x for x in pkgs if
                        self._entropy.is_entropy_package_free(x[1], x[0])])

        return pkgs

    def _pk_add_pkg_type(self, pkgs, important_check=False):
        """
        Expand list of pkg tuples by adding PackageKit package type to it.
        """
        # we have INFO_IMPORTANT, INFO_SECURITY, INFO_NORMAL
        new_pkgs = set()

        for repo, pkg_id, c_repo in pkgs:

            pkg_type = None
            if important_check:
                sys_pkg = self._entropy.validate_package_removal(pkg_id,
                                                                 repo_id=repo)
                if sys_pkg:
                    pkg_type = INFO_IMPORTANT
                else:
                    pkg_type = INFO_NORMAL

            if pkg_type is None:
                if c_repo is self._entropy.installed_repository():
                    info = INFO_INSTALLED
                else:
                    info = INFO_AVAILABLE

            new_pkgs.add((repo, pkg_id, c_repo, pkg_type))

        return new_pkgs

    def _repo_enable(self, repoid):
        excluded_repos = self._settings['repositories']['excluded']
        available_repos = self._settings['repositories']['available']

        if repoid in available_repos:
            # just ignore
            return
        if repoid not in excluded_repos:
            self.error(ERROR_REPO_NOT_FOUND,
                       "Repository %s was not found" % (repoid,))
            return

        try:
            self._entropy.enable_repository(repoid)
        except Exception as err:
            self.error(ERROR_INTERNAL_ERROR,
                       "Failed to enable repository %s: %s" % (repoid, err,))
            return

    def _repo_disable(self, repoid):
        excluded_repos = self._settings['repositories']['excluded']
        available_repos = self._settings['repositories']['available']
        default_repo = self._settings['repositories']['default_repository']

        if repoid in excluded_repos:
            # just ignore
            return
        if repoid not in available_repos:
            self.error(ERROR_REPO_NOT_FOUND,
                       "Repository %s was not found" % (repoid,))
            return

        if repoid == default_repo:
            self.error(ERROR_CANNOT_DISABLE_REPOSITORY,
                       "%s repository can't be disabled" % (repoid,))
            return

        try:
            self._entropy.disable_repository(repoid)
        except Exception as err:
            self.error(ERROR_INTERNAL_ERROR,
                       "Failed to enable repository %s: %s" % (repoid, err,))
            return

    def _get_repo_name(self, repo_db):
        """
        Return repository name (identifier) given an EntropyRepository
        instance.
        """
        if hasattr(repo_db, "name"):
            # new Entropy releases, >=1.0_alpha8
            return repo_db.name
        repo_name = self._repo_name_cache.get(repo_db)
        if repo_name is None:
            repo_name = repo_db.get_plugins_metadata().get("repo_name")
            self._repo_name_cache[repo_db] = repo_name
        return repo_name

    def _etp_get_webservice(self, repository_id):
        """
        Get Entropy Web Services service object (ClientWebService).

        @param entropy_client: Entropy Client interface
        @type entropy_client: entropy.client.interfaces.Client
        @param repository_id: repository identifier
        @type repository_id: string
        @return: the ClientWebService instance
        @rtype: entropy.client.services.interfaces.ClientWebService
        @raise WebService.UnsupportedService: if service is unsupported by
            repository
        """
        factory = self._entropy.WebServices()
        return factory.new(repository_id)

    def _etp_spawn_ugc(self, pkg_data):
        """
        Inform repository maintainers that user fetched packages, if user
        enabled this feature.
        """
        if WebService is None:
            # old entropy library, ignore all
            return

        for repository_id, repo_pkg_keys in pkg_data.items():
            try:
                webserv = self._etp_get_webservice(repository_id)
            except WebService.UnsupportedService:
                continue
            pkg_keys = sorted(repo_pkg_keys)
            try:
                webserv.add_downloads(pkg_keys)
            except WebService.WebServiceException:
                continue

    def _etp_get_category_description(self, category):
        """
        Return translated Entropy packages category description.
        """
        cat_desc = "No description"

        for repository_id in self._entropy.repositories():
            repo = self._entropy.open_repository(repository_id)
            cat_desc_data = repo.retrieveCategoryDescription(category)
            if cat_desc_data:
                if _LOCALE in cat_desc_data:
                    cat_desc = cat_desc_data[_LOCALE]
                elif 'en' in cat_desc_data:
                    cat_desc = cat_desc_data['en']
                break

        return cat_desc

    def _execute_etp_pkgs_remove(self, pkgs, allowdep, autoremove,
                                 simulate=False):
        """
        Execute effective removal (including dep calculation).

        @param pkgs: list of package tuples composed by
            (etp_package_id, EntropyRepository, pk_pkg_id)
        @type pkgs: list
        @param allowdep: Either true or false. If true allow other packages
            to be removed with the package, but false should cause the script
            to abort if other packages are dependent on the package.
        @type allowdep: bool
        @param autoremove: Either true or false. This option is only really
            interesting on embedded devices with a limited amount of flash
            storage. It suggests to the packagekit backend that
            dependencies installed at the same time as the package
            should also be removed if they are not required by
            anything else. For instance, if you install OpenOffice,
            it might download libneon as a dependency. When auto_remove
            is set to true, and you remove OpenOffice then libneon
            will also get removed automatically.
        @keyword simulate: simulate removal if True
        @type simulate: bool
        @type autoremove: bool
        """

        # backend do not implement autoremove
        if autoremove:
            self._log_message(__name__,
                              "autoremove: Entropy backend devs" +
                              "refused to implement this feature")

        self.percentage(0)
        self.status(STATUS_DEP_RESOLVE)

        # check if we have installed pkgs only
        for pkg_id, c_repo, pk_pkg in pkgs:
            if c_repo is not self._entropy.installed_repository():
                self.error(ERROR_DEP_RESOLUTION_FAILED,
                           "Cannot remove a package coming from a repository: %s" % (
                               pk_pkg,))
                return

        match_map = dict((
            (pkg_id, (pkg_id, c_repo, pk_pkg))
            for pkg_id, c_repo, pk_pkg in pkgs))
        matches = [pkg_id for pkg_id, c_repo, pk_pkg in pkgs]

        # calculate deps
        try:
            run_queue = self._entropy.get_removal_queue(matches)
        except DependenciesNotRemovable as err:
            c_repo = self._entropy.installed_repository()
            vpkgs = getattr(err, 'value', set())
            vit_pkgs = ', '.join(sorted(
                [c_repo.retrieveAtom(x[0]) for x in vpkgs],
                key=lambda x: c_repo.retrieveAtom(x)))
            self.error(ERROR_DEP_RESOLUTION_FAILED,
                       "Could not perform remove operation, "
                       "these packages are vital: %s" % (vit_pkgs,))
            return

        added_pkgs = [x for x in run_queue if x not in matches]

        # if there are required packages, allowdep must be on
        if added_pkgs and not allowdep:
            self.error(ERROR_DEP_RESOLUTION_FAILED,
                       "Could not perform remove operation, "
                       "some packages are needed by other packages")
            return

        self.percentage(0)
        self.status(STATUS_REMOVE)
        inst_repo = self._entropy.installed_repository()

        def _generate_map_item(etp_pkg_id):
            _etp_match = (etp_pkg_id, inst_repo)
            return etp_pkg_id, inst_repo, self._etp_to_id(_etp_match)

        # remove
        max_count = len(run_queue)
        count = 0
        for pkg_id in run_queue:
            count += 1

            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__,
                              "_execute_etp_pkgs_remove: done %s/100" % (
                                  percent,))

            self.percentage(percent)
            map_item = match_map.get(pkg_id)
            if map_item is None:
                map_item = _generate_map_item(pkg_id)
            pkg_id, pkg_c_repo, pk_pkg = map_item
            pkg_desc = pkg_c_repo.retrieveDescription(pkg_id)
            self.package(pk_pkg, INFO_REMOVING, pkg_desc)

            if simulate:
                continue

            metaopts = {}
            metaopts['removeconfig'] = False

            package = self._action_factory.get(
                self._action_factory.REMOVE_ACTION,
                (pkg_id, pkg_c_repo.name),
                opts=metaopts)
            x_rc = package.start()
            package.finalize()

            if x_rc != 0:
                pk_pkg = match_map.get(pkg_id, (None, None, None))[2]
                self.error(ERROR_PACKAGE_FAILED_TO_REMOVE,
                           "Cannot remove package: %s" % (pk_pkg,))
                return

        self.finished()

    def _execute_etp_pkgs_fetch(self, pkgs, directory):
        """
        Execute effective packages download.
        """
        self._execute_etp_pkgs_install(pkgs, False, only_fetch=True,
                                       fetch_path=directory, calculate_deps=False)

    def _execute_etp_pkgs_install(self, pkgs, only_trusted, only_fetch=False,
                                  fetch_path=None, calculate_deps=True, simulate=False):
        """
        Execute effective install (including dep calculation).

        @param pkgs: list of package tuples composed by
            (etp_package_id, EntropyRepository, pk_pkg_id)
        @type pkgs: list
        @param only_trusted: only accept trusted pkgs?
        @type only_trusted: bool
        @keyword only_fetch: just fetch packages if True
        @type only_fetch: bool
        @keyword fetch_path: path where to store downloaded packages
        @type fetch_path: string
        @keyword calculate_deps: calculate package dependencies if true and
            add them to queue
        @type calculate_deps: bool
        @keyword simulate: simulate actions if True
        @type simulate: bool
        """
        self.percentage(0)
        self.status(STATUS_RUNNING)

        inst_repo = self._entropy.installed_repository()

        if only_trusted:
            # check if we have trusted pkgs
            for pkg_id, c_repo, pk_pkg in pkgs:
                sha1, sha256, sha512, gpg = c_repo.retrieveSignatures(pkg_id)
                if gpg is None:
                    self.error(ERROR_MISSING_GPG_SIGNATURE,
                               "Package %s is not GPG signed" % (pk_pkg,))
                    return

        matches = [(pkg_id, self._get_repo_name(c_repo),) for
                   pkg_id, c_repo, pk_pkg in pkgs]

        # calculate deps
        if calculate_deps:
            self.status(STATUS_DEP_RESOLVE)

            with inst_repo.shared():
                empty_deps, deep_deps = False, False
                try:
                    queue_obj = self._entropy.get_install_queue(
                        matches, empty_deps, deep_deps)
                    if len(queue_obj) == 2:
                        # new api
                        run_queue, removal_queue = queue_obj
                    else:
                        # old api
                        run_queue, removal_queue, status = queue_obj
                        if status == -2:
                            raise DependenciesNotFound(run_queue)
                        elif status == -3:
                            raise DependenciesCollision(run_queue)
                except DependenciesNotFound as exc:
                    self.error(ERROR_DEP_RESOLUTION_FAILED,
                               "Cannot find the following dependencies: %s" % (
                                   ', '.join(sorted(exc.value)),))
                    return
                except DependenciesCollision:
                    self.error(ERROR_DEP_RESOLUTION_FAILED,
                               "Dependencies collisions, cannot continue")
                    return

        else:
            run_queue = matches
            removal_queue = []

        self.percentage(0)
        self.status(STATUS_DOWNLOAD)

        with inst_repo.shared():
            # Before even starting the fetch
            # make sure that the user accepts their licenses
            # send license signal afterwards
            licenses = self._entropy.get_licenses_to_accept(run_queue)
            if licenses:
                # as per PackageKit specs
                accepted_eulas = os.getenv("accepted_eulas", "").split(";")
                for eula_id in accepted_eulas:
                    if eula_id in licenses:
                        licenses.pop(eula_id)
                        inst_repo.acceptLicense(eula_id)

            for eula_id, eula_pkgs in licenses.items():
                for pkg_id, repo_id in eula_pkgs:
                    pkg_c_repo = self._entropy.open_repository(repo_id)
                    vendor_name = pkg_c_repo.retrieveHomepage(pkg_id)
                    pk_pkg = self._etp_to_id((pkg_id, pkg_c_repo))
                    license_agreement = pkg_c_repo.retrieveLicenseText(eula_id)
                    self.eula_required(eula_id, pk_pkg, vendor_name,
                                       license_agreement)

        if licenses:
            # bye bye, user will have to accept it and get here again
            self.error(EXIT_EULA_REQUIRED,
                       "Following EULAs are not accepted: %s" % (
                           ' '.join(licenses.keys()),))
            return

        # used in case of errors
        with inst_repo.shared():
            match_map = {}
            for pkg_id, repo_id in run_queue:
                pkg_c_repo = self._entropy.open_repository(repo_id)
                match_map[(pkg_id, repo_id,)] = (pkg_id, pkg_c_repo,
                                                 self._etp_to_id((pkg_id, pkg_c_repo)),)

        # fetch pkgs
        max_count = len(run_queue)
        if not only_fetch:
            max_count *= 2
        count = 0
        down_data = {}
        for match in run_queue:
            count += 1

            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "get_packages: done %s/100" % (
                percent,))

            self.percentage(percent)

            with inst_repo.shared():
                pkg_id, pkg_c_repo, pk_pkg = match_map.get(match)
                pkg_repo = pkg_c_repo.name
                pkg_desc = pkg_c_repo.retrieveDescription(pkg_id)
                self.package(pk_pkg, INFO_DOWNLOADING, pkg_desc)

                if simulate:
                    continue

                metaopts = {
                    'dochecksum': True,
                }
                if fetch_path is not None:
                    metaopts['fetch_path'] = fetch_path

                pkg_atom = pkg_c_repo.retrieveAtom(pkg_id)
                obj = down_data.setdefault(pkg_repo, set())
                obj.add(entropy.dep.dep_getkey(pkg_atom))

            package = self._action_factory.get(
                self._action_factory.FETCH_ACTION,
                match,
                opts=metaopts)
            x_rc = package.start()
            package_path = package.package_path()
            package.finalize()

            if x_rc != 0:
                self.error(ERROR_PACKAGE_FAILED_TO_CONFIGURE,
                           "Cannot download package: %s" % (pk_pkg,))
                return

            # emit the file we downloaded
            self.files(pk_pkg, package_path)

        # spawn UGC
        if not simulate:
            self._etp_spawn_ugc(down_data)

        self.percentage(100)
        if only_fetch:
            self.finished()
            return

        # install
        self.status(STATUS_INSTALL)

        for match in run_queue:
            count += 1

            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "get_packages: done %s/100" % (
                percent,))

            self.percentage(percent)

            with inst_repo.shared():
                pkg_id, pkg_c_repo, pk_pkg = match_map.get(match)
                pkg_desc = pkg_c_repo.retrieveDescription(pkg_id)

            self.package(pk_pkg, INFO_INSTALLING, pkg_desc)

            if simulate:
                continue

            metaopts = {
                'removeconfig': False,
            }
            # setup install source
            if match in matches:
                metaopts['install_source'] = etpConst[
                    'install_sources']['user']
            else:
                metaopts['install_source'] = \
                    etpConst['install_sources']['automatic_dependency']

            package = self._action_factory.get(
                self._action_factory.INSTALL_ACTION,
                match, opts=metaopts)
            x_rc = package.start()
            package.finalize()

            if x_rc != 0:
                self.error(ERROR_PACKAGE_FAILED_TO_INSTALL,
                           "Cannot install package: %s" % (pk_pkg,))
                return

        self._config_files_message()
        self.finished()


class PackageKitEntropyClient(Client):

    """ PackageKit Entropy Client subclass """

    _pk_progress = None
    _pk_message = None

    def init_singleton(self):
        Client.init_singleton(self, url_fetcher=PkUrlFetcher)

    @classmethod
    def output(cls, text, header="", footer="", back=False,
               importance=0, level="info", count=None, percent=False):
        """
        Reimplemented from entropy.output.TextInterface.
        """
        message_func = PackageKitEntropyClient._pk_message
        if message_func is not None:
            message_func(text)

        progress = PackageKitEntropyClient._pk_progress
        if progress is None:
            return
        if count is None:
            return

        cur, tot = count[0], count[1]
        progress(PackageKitEntropyMixin.get_percentage(cur, tot))

# in this way, any singleton class that tries to directly load Client
# gets PackageKitEntropyClient in change
Client.__singleton_class__ = PackageKitEntropyClient


class PkUrlFetcher(UrlFetcher):

    _pk_progress = None
    _last_t = time.time()

    def __init__(self, *args, **kwargs):
        self.__average = 0
        self.__downloadedsize = 0
        self.__remotesize = 0
        self.__datatransfer = 0
        UrlFetcher.__init__(self, *args, **kwargs)

    def handle_statistics(self, th_id, downloaded_size, total_size,
                          average, old_average, update_step, show_speed, data_transfer,
                          time_remaining, time_remaining_secs):
        self.__average = average
        self.__downloadedsize = downloaded_size
        self.__remotesize = total_size
        self.__datatransfer = data_transfer

    def update(self):
        if PkUrlFetcher._pk_progress is None:
            return

        last_t = PkUrlFetcher._last_t
        if (time.time() - last_t) > 1:
            myavg = abs(int(round(float(self.__average), 1)))
            cur_prog = int(float(self.__average) / 100)
            PkUrlFetcher._pk_progress(cur_prog)
            PkUrlFetcher._last_t = time.time()


class PackageKitEntropyBackend(PackageKitBaseBackend, PackageKitEntropyMixin):

    _log_fname = os.path.join(etpConst['syslogdir'], "packagekit.log")

    # Entropy <-> PackageKit groups map
    GROUP_MAP = {
        'accessibility': GROUP_ACCESSIBILITY,
        'development': GROUP_PROGRAMMING,
        'games': GROUP_GAMES,
        'gnome': GROUP_DESKTOP_GNOME,
        'kde': GROUP_DESKTOP_KDE,
        'lxde': GROUP_DESKTOP_OTHER,
        'multimedia': GROUP_MULTIMEDIA,
        'networking': GROUP_NETWORK,
        'office': GROUP_OFFICE,
        'science': GROUP_SCIENCE,
        'system': GROUP_SYSTEM,
        'security': GROUP_SECURITY,
        'x11': GROUP_OTHER,
        'xfce': GROUP_DESKTOP_XFCE,
        'unknown': GROUP_UNKNOWN,
    }

    def __init__(self, args):
        PackageKitEntropyMixin.__init__(self)
        PackageKitBaseBackend.__init__(self, args)

        self._real_settings = None
        self._real_settings_lock = threading.Lock()

        self._real_action_factory = None
        self._real_action_factory_lock = threading.Lock()

        self._real_entropy_log = None
        self._real_entropy_log_lock = threading.Lock()

        self._real_entropy = None
        self._real_entropy_lock = threading.Lock()

        self.doLock()
        self._repo_name_cache = {}
        PackageKitEntropyClient._pk_progress = self.percentage
        PackageKitEntropyClient._pk_message = self._generic_message

    @property
    def _entropy(self):
        """
        Return the PackageKitEntropyClient instance.
        """
        if self._real_entropy is None:
            with self._real_entropy_lock:

                if self._real_entropy is None:
                    self._real_entropy = PackageKitEntropyClient()

        return self._real_entropy

    @property
    def _entropy_log(self):
        """
        Return the Entropy LogFile instance.
        """
        if self._real_entropy_log is None:
            with self._real_entropy_log_lock:
                if self._real_entropy_log is None:
                    self._real_entropy_log = LogFile(
                        level=self._settings['system']['log_level'],
                        filename=self._log_fname,
                        header="[packagekit]")

        return self._real_entropy_log

    @property
    def _action_factory(self):
        """
        Return a PackageActionFactory instance.
        """
        if self._real_action_factory is None:
            with self._real_action_factory_lock:

                if self._real_action_factory is None:
                    factory = self._entropy.PackageActionFactory()
                    self._real_action_factory = factory

        return self._real_action_factory

    @property
    def _settings(self):
        """
        return a SystemSettings instance.
        """
        if self._real_settings is None:
            with self._real_settings_lock:
                if self._real_settings is None:
                    self._real_settings = SystemSettings()

        return self._real_settings

    def unLock(self):
        PackageKitBaseBackend.unLock(self)

    def _convert_date_to_iso8601(self, unix_time_str):
        unix_time = float(unix_time_str)
        ux_t = time.localtime(unix_time)
        formatted = time.strftime('%Y-%m-%dT%H:%M:%S', ux_t)
        return formatted

    def _generic_message(self, message):
        # FIXME: this doesn't work, it seems there's no way to
        # print something to user while pkcon runs.
        # self.message(MESSAGE_UNKNOWN, message)
        self._log_message(__name__, "_generic_message:", decolorize(message))

    def _config_files_message(self):
        updates = self._entropy.ConfigurationUpdates()
        scandata = updates.get(quiet=True)
        has_updates = len(scandata) > 0

        if has_updates:
            message = "Some configuration files need updating."
            message += ";You should use 'equo conf update' to update them"
            message += ";If you can't do that, ask your system administrator."
            self._log_message(__name__, message, decolorize(message))

    def _package(self, pkg_match, info=None):

        # package_id = (package_identifier, EntropyRepository)
        pkg_id, c_repo = pkg_match
        desc = c_repo.retrieveDescription(pkg_id)

        if not info:
            if c_repo is self._entropy.installed_repository():
                info = INFO_INSTALLED
            else:
                info = INFO_AVAILABLE
        return self.package(self._etp_to_id(pkg_match), info, desc)

    def _is_only_trusted(self, transaction_flags):
        return (TRANSACTION_FLAG_ONLY_TRUSTED in transaction_flags) or (
            TRANSACTION_FLAG_SIMULATE in transaction_flags)

    def _is_simulate(self, transaction_flags):
        return TRANSACTION_FLAG_SIMULATE in transaction_flags

    def _is_only_download(self, transaction_flags):
        return TRANSACTION_FLAG_ONLY_DOWNLOAD in transaction_flags

    @sharedreslock
    @sharedinstlock
    def depends_on(self, filters, package_ids, recursive):
        self._log_message(__name__, "depends_on: got %s and %s and %s" % (
            filters, package_ids, recursive,))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(0)

        pkgs = set()
        for pk_pkg in package_ids:

            pkg = self._id_to_etp(pk_pkg)
            if pkg is None:  # wtf!
                self._log_message(__name__, "depends_on: cannot match %s" % (
                    pk_pkg,))
                continue

            self._log_message(__name__, "depends_on: translated %s => %s" % (
                pk_pkg, pkg,))

            pkg_id, repo_db = pkg
            repo = self._get_repo_name(repo_db)
            pkgs.add((repo, pkg_id, repo_db,))

        matches = [(y, x) for x, y, z in pkgs]
        self._log_message(__name__, "depends_on: raw matches => %s" % (
            matches,))

        empty = False
        deep = False
        try:
            queue_obj = self._entropy.get_install_queue(matches,
                                                        empty, deep, recursive=recursive)
            if len(queue_obj) == 2:
                # new api
                install, removal = queue_obj
            else:
                # old api
                install, removal, status = queue_obj
                if status == -2:
                    raise DependenciesNotFound(install)
                elif status == -3:
                    raise DependenciesCollision(install)
        except DependenciesNotFound as exc:
            self.error(ERROR_DEP_RESOLUTION_FAILED,
                       "Dependencies not found: %s" % (sorted(exc.value),))
            return
        except DependenciesCollision:
            self.error(ERROR_DEP_RESOLUTION_FAILED,
                       "Dependencies collisions, cannot continue")
            return

        # transform install into (repo, pkg_id, c_repo) list
        install = [(y, x, self._entropy.open_repository(y),) for x, y in
                   install]
        # transform remove the same way
        inst_pkg_r_id = PackageKitEntropyMixin.INST_PKGS_REPO_ID
        removal = [(inst_pkg_r_id, x, self._entropy.installed_repository())
                   for x in removal]

        pkgs = set(install + removal)

        self._log_message(__name__, "depends_on: matches %s" % (
            pkgs,))

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def get_details(self, package_ids):

        self._log_message(__name__, "get_details: got %s" % (package_ids,))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(0)

        count = 0
        max_count = len(package_ids)
        for pk_pkg in package_ids:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "get_packages: done %s/100" % (
                percent,))

            self.percentage(percent)
            pkg = self._id_to_etp(pk_pkg)
            if pkg is None:
                self.error(ERROR_PACKAGE_NOT_FOUND,
                           "Package %s was not found" % (pk_pkg,))
                continue
            pkg_id, c_repo = pkg

            category = c_repo.retrieveCategory(pkg_id)
            lic = c_repo.retrieveLicense(pkg_id)
            homepage = c_repo.retrieveHomepage(pkg_id)
            description = c_repo.retrieveDescription(pkg_id)
            if (category is None) or (description is None):
                self.error(ERROR_PACKAGE_NOT_FOUND,
                           "Package %s was not found in repository" % (pk_pkg,))
                continue

            self.details(pk_pkg, '', lic, self._get_pk_group(category),
                         description, homepage, self._get_pkg_size(pkg))

        self.percentage(100)

    def _etp_get_package_categories(self):
        categories = set()
        for repository_id in self._entropy.repositories():
            repo_db = self._entropy.open_repository(repository_id)
            try:
                categories.update(repo_db.listAllCategories())
            except EntropyRepositoryError:
                # on broken repos this might cause issues
                continue
        return sorted(categories)

    @sharedreslock
    @sharedinstlock
    def get_categories(self):

        self._log_message(__name__, "get_categories: called")

        self.status(STATUS_QUERY)
        self.allow_cancel(True)

        categories = self._etp_get_package_categories()
        if not categories:
            self.error(ERROR_GROUP_LIST_INVALID, "no package categories")
            return

        for name in categories:
            name = const_convert_to_rawstring(name)

            summary = self._etp_get_category_description(name)
            summary = const_convert_to_rawstring(summary, "utf-8")

            f_name = "/usr/share/pixmaps/entropy/%s.png" % (name,)
            if os.path.isfile(f_name) and os.access(f_name, os.R_OK):
                icon = name
            else:
                icon = const_convert_to_rawstring("image-missing")

            nothing = const_convert_to_rawstring("")
            cat_id = name  # same thing

            self._log_message(__name__, "get_categories: pushing",
                              nothing, cat_id, name, summary, icon)

            self.category(nothing, cat_id, name, summary, icon)

    @sharedreslock
    @sharedinstlock
    def get_files(self, package_ids):

        self._log_message(__name__, "get_files: got %s" % (package_ids,))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(0)

        pkgs = []
        for pk_pkg in package_ids:

            pkg = self._id_to_etp(pk_pkg)
            if pkg is None:  # wtf!
                self.error(ERROR_PACKAGE_NOT_FOUND,
                           "Package %s was not found" % (pk_pkg,))
                self._log_message(__name__, "get_files: cannot match %s" % (
                    pk_pkg,))
                continue

            self._log_message(__name__, "get_files: translated %s => %s" % (
                pk_pkg, pkg,))

            pkg_id, repo_db = pkg
            repo = self._get_repo_name(repo_db)
            pkgs.append((repo, pkg_id, repo_db, pk_pkg))

        count = 0
        max_count = len(pkgs)
        for repo, pkg_id, repo_db, pk_pkg in pkgs:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "get_files: done %s/100" % (
                percent,))

            self.percentage(percent)
            files = repo_db.retrieveContent(pkg_id, order_by='file')
            files = ";".join(files)
            self.files(pk_pkg, files)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def get_packages(self, filters):

        self._log_message(__name__, "get_packages: got %s" % (
            filters,))

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        repos = self._get_all_repos()

        pkgs = set()
        count = 0
        max_count = len(repos)
        for repo_db, repo in repos:

            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(
                __name__, "get_packages: done %s/100" % (percent,))

            self.percentage(percent)
            try:
                pkg_ids = repo_db.listAllIdpackages()
            except AttributeError:
                pkg_ids = repo_db.listAllPackageIds()
            pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    def get_repo_list(self, filters):

        self._log_message(__name__, "get_repo_list: got %s" % (filters,))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(None)

        excluded_repos = self._settings['repositories']['excluded']
        available_repos = self._settings['repositories']['available']
        default_repo = self._settings['repositories']['default_repository']

        all_repos = sorted(excluded_repos.keys() + available_repos.keys())
        metadata = []
        for repo_id in all_repos:

            repo_data = available_repos.get(repo_id,
                                            excluded_repos.get(repo_id))
            if repo_data is None:  # wtf?
                continue

            enabled = self._is_repository_enabled(repo_id)
            desc = repo_data['description']
            devel = repo_id != default_repo
            metadata.append((repo_id, desc, enabled, devel))

        if FILTER_NOT_DEVELOPMENT in filters:
            metadata = [x for x in metadata if not x[3]]

        for repo_id, desc, enabled, devel in metadata:
            self.repo_detail(repo_id, desc, enabled)

    @sharedreslock
    @sharedinstlock
    def required_by(self, filters, package_ids, recursive):
        self._log_message(__name__, "required_by: got %s and %s and %s" % (
            filters, package_ids, recursive))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(0)

        pkgs = set()
        for pk_pkg in package_ids:

            pkg = self._id_to_etp(pk_pkg)
            if pkg is None:  # wtf!
                self._log_message(__name__, "required_by: cannot match %s" % (
                    pk_pkg,))
                continue

            self._log_message(__name__, "required_by: translated %s => %s" % (
                pk_pkg, pkg,))

            pkg_id, repo_db = pkg
            repo = self._get_repo_name(repo_db)
            pkgs.add((repo, pkg_id, repo_db,))

        matches = [(y, x) for x, y, z in pkgs]

        self._log_message(__name__, "required_by: cooked => %s" % (
            matches,))

        empty = False
        deep = False
        reverse_deps = self._entropy.get_reverse_queue(matches,
                                                       deep=deep, recursive=recursive)

        self._log_message(__name__, "required_by: reverse_deps => %s" % (
            reverse_deps,))

        pkgs = set([(y, x, self._entropy.open_repository(y),) for x, y in
                    reverse_deps])

        self._log_message(__name__, "required_by: matches %s" % (
            pkgs,))

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def get_update_detail(self, package_ids):

        self._log_message(__name__, "get_update_detail: got %s" % (
            package_ids,))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(0)

        count = 0
        max_count = len(package_ids)
        default_repo = self._settings['repositories']['default_repository']
        inst_repo = self._entropy.installed_repository()
        for pk_pkg in package_ids:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "get_update_detail: done %s/100" % (
                percent,))

            self.percentage(percent)
            pkg = self._id_to_etp(pk_pkg)
            if pkg is None:
                self._log_message(__name__,
                                  "could not find %s" % (pk_pkg,))
                continue
            pkg_id, c_repo = pkg
            repo_name = self._get_repo_name(c_repo)

            updates = []
            keyslot = c_repo.retrieveKeySlotAggregated(pkg_id)
            matches, m_rc = self._entropy.atom_match(
                keyslot, multi_match=True,
                multi_repo=True)
            for m_pkg_id, m_repo_id in matches:
                if (m_pkg_id, m_repo_id) == (pkg_id, repo_name):
                    continue  # fliter myself
                m_c_repo = self._entropy.open_repository(m_repo_id)
                updates.append(self._etp_to_id((m_pkg_id, m_c_repo)))

            obsoletes = ""
            bugzilla_url = "http://bugs.sabayon.org"
            cve_url = ""
            vendor_url = c_repo.retrieveHomepage(pkg_id)
            changelog = c_repo.retrieveChangelog(pkg_id)
            updates = "&".join(updates)

            # when package has been issued
            issued = self._convert_date_to_iso8601(
                c_repo.retrieveCreationDate(pkg_id))

            # when package has been updated on system
            # search inside installed pkgs db
            updated = ''
            c_id, c_rc = inst_repo.atomMatch(keyslot)
            if c_rc == 0:
                updated = self._convert_date_to_iso8601(
                    inst_repo.retrieveCreationDate(c_id))

            update_message = "Update"
            state = UPDATE_STATE_STABLE
            if repo_name != default_repo:
                state = UPDATE_STATE_TESTING

            self._log_message(__name__, "get_update_detail: issuing %s" % (
                (pk_pkg, updates, obsoletes, vendor_url, bugzilla_url),))

            self.update_detail(pk_pkg, updates, obsoletes, vendor_url,
                               bugzilla_url, cve_url, "none", update_message, changelog,
                               state, issued, updated)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def get_distro_upgrades(self):
        """
        FIXME: should this return only system updates? (pkgs marked as syspkgs)
        Not implemented atm
        """
        PackageKitBaseBackend.get_distro_upgrades(self)

    @sharedreslock
    @sharedinstlock
    def get_updates(self, filters):

        self.status(STATUS_INFO)
        self.allow_cancel(True)

        # this is the part that takes time
        self.percentage(0)
        try:
            outcome = self._entropy.calculate_updates()

            if isinstance(outcome, dict):
                update, remove, fine, spm_fine = outcome['update'], \
                    outcome['remove'], outcome['fine'], outcome['spm_fine']
            else:
                update, remove, fine, spm_fine = outcome

        except SystemDatabaseError as err:
            self.error(ERROR_DEP_RESOLUTION_FAILED,
                       "System Repository error: %s" % (err,))
            return
        self.percentage(100)

        pkgs = set()
        count = 0
        max_count = len(update)
        for pkg_id, repo_id in update:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "get_updates: done %s/100" % (
                percent,))

            self.percentage(percent)
            repo_db = self._entropy.open_repository(repo_id)
            pkgs.add((repo_id, pkg_id, repo_db))

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs, important_check=True)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    def install_files(self, transaction_flags, inst_files):

        only_trusted = self._is_only_trusted(transaction_flags)
        simulate = self._is_simulate(transaction_flags)

        self._log_message(__name__, "install_files: got", only_trusted,
                          "and", inst_files, "and", simulate)

        self.allow_cancel(True)
        self.status(STATUS_RUNNING)

        for etp_file in inst_files:
            if not os.path.exists(etp_file):
                self.error(ERROR_FILE_NOT_FOUND,
                           "%s could not be found" % (etp_file,))
                return

            if not entropy.tools.is_entropy_package_file(etp_file):
                self.error(ERROR_INVALID_PACKAGE_FILE,
                           "Only Entropy files are supported")
                return

        pkg_ids = []

        for etp_file in inst_files:
            try:
                atomsfound = self._entropy.add_package_repository(etp_file)
            except EntropyPackageException:
                atomsfound = None

            if not atomsfound:
                self.error(ERROR_INVALID_PACKAGE_FILE,
                           "Error while trying to add %s repository" % (etp_file,))
                return
            for idpackage, repo_id in atomsfound:
                pkg_ids.append((idpackage, repo_id))

        self._log_message(__name__, "install_files: generated", pkg_ids)

        pkgs = []
        for pkg_id, repo_id in pkg_ids:
            if pkg_id == -1:  # wtf!?
                self.error(ERROR_INVALID_PACKAGE_FILE,
                           "Repo was added but package %s is not found" % (
                               (pkg_id, repo_id),))
                return
            repo_db = self._entropy.open_repository(repo_id)
            pkg = (pkg_id, repo_db)
            pk_pkg = self._etp_to_id(pkg)
            pkgs.append((pkg[0], pkg[1], pk_pkg,))

        self._execute_etp_pkgs_install(pkgs, only_trusted, simulate=simulate)

    @sharedreslock
    def install_packages(self, transaction_flags, pk_pkgs):

        only_trusted = self._is_only_trusted(transaction_flags)
        simulate = self._is_simulate(transaction_flags)
        only_download = self._is_only_download(transaction_flags)

        self._log_message(__name__, "install_packages: got", only_trusted,
                          "and", pk_pkgs, "and", simulate)

        self.status(STATUS_RUNNING)
        self.allow_cancel(True)

        inst_repo = self._entropy.installed_repository()

        with inst_repo.shared():
            pkgs = []
            for pk_pkg in pk_pkgs:
                pkg = self._id_to_etp(pk_pkg)
                if pkg is None:
                    self.error(ERROR_PACKAGE_NOT_FOUND,
                               "Package %s was not found" % (pk_pkg,))
                    continue
                pkgs.append((pkg[0], pkg[1], pk_pkg,))

        self._execute_etp_pkgs_install(
            pkgs, only_trusted, simulate=simulate,
            only_fetch=only_download, calculate_deps=not only_download)

    @sharedreslock
    def download_packages(self, directory, package_ids):

        self._log_message(__name__, "download_packages: got %s and %s" % (
            directory, package_ids,))

        self.status(STATUS_RUNNING)
        self.allow_cancel(True)

        inst_repo = self._entropy.installed_repository()
        pkgs = []

        with inst_repo.shared():
            for pk_pkg in package_ids:
                pkg = self._id_to_etp(pk_pkg)
                if pkg is None:
                    self.error(ERROR_PACKAGE_NOT_FOUND,
                               "Package %s was not found" % (pk_pkg,))
                    continue
                pkgs.append((pkg[0], pkg[1], pk_pkg,))

        self._execute_etp_pkgs_fetch(pkgs, directory)

    def _etp_update_repository_stats(self, repository_ids):
        """
        Update repository download statistics.
        """
        if WebService is None:
            # old entropy library, ignore all
            return

        for repository_id in repository_ids:
            try:
                webserv = self._etp_get_webservice(repository_id)
            except WebService.UnsupportedService:
                continue
            try:
                webserv.add_downloads(repository_id, [repository_id])
            except WebService.WebServiceException:
                continue

    @exclusivereslock
    def refresh_cache(self, force):

        self.status(STATUS_REFRESH_CACHE)
        self.allow_cancel(False)
        self.percentage(0)

        repo_intf = None
        repo_identifiers = sorted(self._settings['repositories']['available'])
        try:
            repo_intf = self._entropy.Repositories(repo_identifiers,
                                                   force=force)
        except AttributeError:
            self.error(ERROR_REPO_CONFIGURATION_ERROR, traceback.format_exc())
        except Exception as err:
            self.error(ERROR_INTERNAL_ERROR, traceback.format_exc())

        if repo_intf is None:
            return

        ex_rc = repo_intf.sync()
        if not ex_rc:
            self._etp_update_repository_stats(repo_identifiers)
        else:
            self._log_message(__name__, "Cannot update repositories!")

        self.percentage(100)

    @sharedreslock
    def remove_packages(self, transaction_flags, package_ids, allowdep, autoremove):
        return self._remove_packages(transaction_flags, package_ids, allowdep, autoremove)

    def _remove_packages(self, transaction_flags, pk_pkgs, allowdep, autoremove):

        self._log_message(__name__, "remove_packages: got %s and %s and %s" % (
            allowdep, autoremove, pk_pkgs,))
        simulate = self._is_simulate(transaction_flags)

        self.status(STATUS_RUNNING)
        self.allow_cancel(True)

        inst_repo = self._entropy.installed_repository()
        pkgs = []

        with inst_repo.shared():
            for pk_pkg in pk_pkgs:
                pkg = self._id_to_etp(pk_pkg)
                if pkg is None:
                    self.error(ERROR_UPDATE_NOT_FOUND,
                               "Package %s was not found" % (pk_pkg,))
                    continue
                pkgs.append((pkg[0], pkg[1], pk_pkg,))

        self._execute_etp_pkgs_remove(pkgs, allowdep, autoremove,
                                      simulate=simulate)

    @exclusivereslock
    def repo_enable(self, repoid, enable):

        self._log_message(__name__, "repo_enable: got %s and %s" % (
            repoid, enable,))

        self.status(STATUS_INFO)
        self.allow_cancel(True)
        self.percentage(None)

        if enable:
            self._repo_enable(repoid)
        else:
            self._repo_disable(repoid)

        self._log_message(__name__, "repo_enable: done")

    @sharedreslock
    @sharedinstlock
    def resolve(self, filters, values):

        self._log_message(__name__, "resolve: got %s and %s" % (
            filters, values,))

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        repos = self._get_all_repos()

        pkgs = set()
        count = 0
        max_count = len(repos)
        for repo_db, repo in repos:

            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "resolve: done %s/100" % (
                percent,))

            self.percentage(percent)
            for key in values:
                pkg_ids, pkg_rc = repo_db.atomMatch(key, multiMatch=True)
                pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def search_details(self, filters, values):

        values = self._encode_string_list(values)

        self._log_message(__name__, "search_details: got %s and %s" % (
            filters, values,))

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        repos = self._get_all_repos()

        pkgs = set()
        count = 0
        max_count = len(repos)
        for repo_db, repo in repos:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "search_details: done %s/100" % (
                percent,))

            self.percentage(percent)
            for key in values:
                pkg_ids = repo_db.searchDescription(key,
                                                    just_id=True)
                pkg_ids |= repo_db.searchHomepage(key, just_id=True)
                pkg_ids |= repo_db.searchLicense(key, just_id=True)
                if not pkg_ids:
                    pkg_ids = repo_db.searchPackages(key, just_id=True)
                pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def search_file(self, filters, values):

        values = self._encode_string_list(values)

        self._log_message(__name__, "search_file: got %s and %s" % (
            filters, values,))

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        reverse_symlink_map = self._settings['system_rev_symlinks']
        repos = self._get_all_repos()

        pkgs = set()
        count = 0
        max_count = len(repos)
        for repo_db, repo in repos:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "search_file: done %s/100" % (
                percent,))

            self.percentage(percent)

            for key in values:

                like = False
                # wildcard support
                if key.find("*") != -1:
                    key.replace("*", "%")
                    like = True

                pkg_ids = repo_db.searchBelongs(key, like=like)
                if not pkg_ids:
                    # try real path if possible
                    pkg_ids = repo_db.searchBelongs(os.path.realpath(key),
                                                    like=like)
                if not pkg_ids:
                    # try using reverse symlink mapping
                    for sym_dir in reverse_symlink_map:
                        if key.startswith(sym_dir):
                            for sym_child in reverse_symlink_map[sym_dir]:
                                my_file = sym_child + key[len(sym_dir):]
                                pkg_ids = repo_db.searchBelongs(my_file,
                                                                like=like)
                                if pkg_ids:
                                    break

                pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def search_group(self, filters, values):

        values = self._encode_string_list(values)

        self._log_message(__name__, "search_group: got %s and %s" % (
            filters, values,))

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        repos = self._get_all_repos()

        entropy_groups = self._entropy.get_package_groups()
        all_matched_categories = set()
        for e_data in entropy_groups.values():
            all_matched_categories.update(e_data['categories'])
        all_matched_categories = sorted(all_matched_categories)

        selected_categories = set()
        for group in values:
            entropy_group = self._get_entropy_group(group)
            # group_data is None when there's no matching group
            group_data = entropy_groups.get(entropy_group)
            if group_data is not None:
                selected_categories.update(group_data['categories'])

        # if selected_categories is empty, then pull in pkgs with non matching
        # category in all_matched_categories

        pkgs = set()
        count = 0
        max_count = len(repos)
        for repo_db, repo in repos:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "search_group: done %s/100" % (
                percent,))

            self.percentage(percent)
            repo_all_cats = repo_db.listAllCategories()

            if hasattr(repo_db, "listPackageIdsInCategory"):
                if selected_categories:
                    etp_cats = set((x for x in repo_all_cats
                                    if x in selected_categories))
                else:
                    # get all etp categories excluding all_matched_categories
                    etp_cats = set((x for x in repo_all_cats
                                    if x not in all_matched_categories))

                for category in etp_cats:
                    pkg_ids = repo_db.listPackageIdsInCategory(category)
                    pkgs.update((repo, x, repo_db,) for x in pkg_ids)

            else:
                # backward compatibility
                if selected_categories:
                    etp_cat_ids = set([cat_id for cat_id, cat_name in
                                       repo_all_cats if cat_name in selected_categories])
                else:
                    # get all etp category ids excluding all_matched_categories
                    etp_cat_ids = set([cat_id for cat_id, cat_name in
                                       repo_all_cats if cat_name not in
                                       all_matched_categories])

                for cat_id in etp_cat_ids:
                    try:
                        pkg_ids = repo_db.listIdPackagesInIdcategory(cat_id)
                    except AttributeError:
                        pkg_ids = repo_db.listPackageIdsInCategoryId(cat_id)
                    pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    def search_name(self, filters, values):

        values = self._encode_string_list(values)

        self._log_message(__name__, "search_name: got %s and %s" % (
            filters, values,))

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        repos = self._get_all_repos()

        pkgs = set()
        count = 0
        max_count = len(repos)
        for repo_db, repo in repos:
            count += 1
            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "search_name: done %s/100" % (
                percent,))

            self.percentage(percent)
            for key in values:
                pkg_ids = repo_db.searchPackages(key, just_id=True)
                pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    def update_packages(self, transaction_flags, pk_pkgs):

        only_trusted = self._is_only_trusted(transaction_flags)
        simulate = self._is_simulate(transaction_flags)
        only_download = self._is_only_download(transaction_flags)

        self._log_message(__name__, "update_packages: got", only_trusted,
                          "and", pk_pkgs, "and", simulate)

        self.status(STATUS_RUNNING)
        self.allow_cancel(True)

        inst_repo = self._entropy.installed_repository()
        pkgs = []

        with inst_repo.shared():
            for pk_pkg in pk_pkgs:
                pkg = self._id_to_etp(pk_pkg)
                if pkg is None:
                    self.error(ERROR_UPDATE_NOT_FOUND,
                               "Package %s was not found" % (pk_pkg,))
                    continue
                pkgs.append((pkg[0], pkg[1], pk_pkg,))

        self._execute_etp_pkgs_install(
            pkgs, only_trusted, simulate=simulate,
            only_fetch=only_download, calculate_deps=not only_download)

    def _what_provides_mime(self, filters, values):

        self.status(STATUS_QUERY)
        self.allow_cancel(True)
        self.percentage(0)

        repos = self._get_all_repos()

        inst_repo = self._entropy.installed_repository()
        pkgs = set()
        max_count = len(repos)

        for count, (repo_db, repo) in enumerate(repos, 1):

            percent = PackageKitEntropyMixin.get_percentage(count, max_count)

            self._log_message(__name__, "_what_provides_mime: done %s/100" % (
                percent,))

            self.percentage(percent)
            for key in values:
                pkg_ids = repo_db.searchProvidedMime(key)
                pkgs.update((repo, x, repo_db,) for x in pkg_ids)

        # now filter
        pkgs = self._pk_filter_pkgs(pkgs, filters)
        pkgs = self._pk_add_pkg_type(pkgs)
        # now feed stdout
        self._pk_feed_sorted_pkgs(pkgs)

        self.percentage(100)

    @sharedreslock
    @sharedinstlock
    def what_provides(self, filters, provides_type, values):
        """
        PROVIDES_ANY = "any"
        # PROVIDES_CODEC = "codec"
        # PROVIDES_FONT = "font"
        # PROVIDES_HARDWARE_DRIVER = "driver"
        # PROVIDES_MIMETYPE = "mimetype"
        PROVIDES_MODALIAS = "modalias"
        PROVIDES_POSTSCRIPT_DRIVER = "postscript-driver"
        PROVIDES_UNKNOWN = "unknown"
        """
        values = self._encode_string_list(values)

        self._log_message(__name__, "what_provides: got", filters,
                          "and", provides_type, "and", values)

        if provides_type == PROVIDES_MIMETYPE:
            # search packages providing given mime-types
            return self._what_provides_mime(filters, values)

        # elif provides_type == PROVIDES_HARDWARE_DRIVER:
        # search packages providing given hardware driver
        #    pass

        # elif provides_type == PROVIDES_FONT:
        # search packages providing given system font
        #    pass

        # elif provides_type == PROVIDES_CODEC:
        #    pass

        else:
            self.error(ERROR_NOT_SUPPORTED,
                       "This function is not implemented in this backend")


def main():
    backend = PackageKitEntropyBackend("")
    backend.dispatcher(sys.argv[1:])

if __name__ == "__main__":
    main()
