# Copyright (c) 2013 Craig Tracey <craigtracey@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.import argparse
#

import argparse
import datetime
import errno
import glob
import os
import re
import shutil
import sys
import tarfile
import tempfile

import git
import giturlparse
import yaml


def _fetch_git_repo(repo, ref):
    home = os.path.expanduser("~")
    reponimousdir = os.path.join(home, ".reponimous")
    if not os.path.isdir(reponimousdir):
        os.makedirs(reponimousdir)

    cleanref = re.sub('/', '-', ref)
    parsedrepo = giturlparse.parse(repo, False)
    repodirname = os.path.join(reponimousdir, "%s-%s-%s" %
                               (parsedrepo.owner, parsedrepo.repo, cleanref))

    if not os.path.isdir(repodirname):
        git.Git().clone(repo, repodirname)

    gitrepo = git.Repo(repodirname)
    gitrepo.git.checkout(ref)

    if not gitrepo.head.is_detached:
        gitrepo.git.pull()

    return repodirname


def _force_symlink(src, dst):
    try:
        os.symlink(src, dst)
    except OSError, e:
        if e.errno == errno.EEXIST:
            os.remove(dst)
            os.symlink(src, dst)


def _symlink_all_content(src, dst):
    for dirname, subdirs, filenames in os.walk(src):
        srcbase = dirname[len(src) + 1:]
        dstbase = os.path.join(dst, dirname[len(src) + 1:])
        for subdir in subdirs:
            if subdir.startswith('.git'):
                continue
            os.makedirs(os.path.join(dstbase, subdir))
        for filename in filenames:
            if filename.startswith('.git'):
                continue
            os.symlink(
                os.path.join(src, srcbase, filename),
                os.path.join(dstbase, dirname[len(src) + 1:1], filename))


def _link_overlay_files(srcdir, src, dstdir, dst):
    if not isinstance(src, list):
        src = [src]

    srcfiles = []
    for s in src:
        srcfiles += glob.glob(os.path.join(srcdir, s))

    symdst = None
    for filename in srcfiles:

        if not os.path.exists(filename):
            print "WARNING: Source file '%s' does not exist. Skipping."
            continue

        if os.path.basename(filename).startswith('.git'):
            continue

        if os.path.isfile(filename):
            filedstdir = None
            filedstname = None
            if not dst:
                filedstdir = os.path.join(
                    dstdir, os.path.dirname(filename)[len(srcdir) + 1:])
                filedstname = os.path.basename(filename)
            elif os.path.isdir(os.path.join(dstdir, dst)) or dst.endswith('/'):
                filedstdir = os.path.join(dstdir, dst)
                filedstname = os.path.basename(filename)
            elif not os.path.isdir(os.path.join(dstdir, dst)):
                filedstdir = os.path.dirname(os.path.join(dstdir, dst))
                filedstname = os.path.basename(os.path.join(dstdir, dst))

            symdst = os.path.join(filedstdir, filedstname)
            if not os.path.exists(filedstdir):
                os.makedirs(filedstdir)

        else:
            if os.path.isdir(os.path.join(dstdir, dst)) or dst.endswith('/'):
                linkdstdir = os.path.join(dstdir, dst,
                                          os.path.basename(filename))
                _force_symlink(filename, linkdstdir)
                continue

            if not dst:
                linkdstdir = os.path.join(
                    dstdir, os.path.dirname(filename)[len(srcdir) + 1:])
            else:
                linkdstdir = os.path.join(dstdir, dst)

            # make sure the parent paths are there
            symdst = linkdstdir
            if not os.path.exists(linkdstdir):
                os.makedirs(linkdstdir)

        _force_symlink(filename, symdst)


def _create_timestamp_name(fmt='%Y-%m-%dT%H:%M:%S%z'):
    return datetime.datetime.now().strftime(fmt)


def _archive(src, name=None, dst=None):
    archivename = "reponimous-%s.tgz" % _create_timestamp_name()
    if name:
        archivename = "%s.tgz" % name

    if not dst:
        dst = os.getcwd()

    if not os.path.exists(dst):
        os.makedirs(dst)

    archivepath = os.path.join(dst, archivename)
    tar = tarfile.open(archivepath, "w:gz", dereference=True)

    for item in os.listdir(src):
        tar.add(os.path.join(src, item), arcname=os.path.basename(item))
    tar.close()
    return archivepath


def _create_merged_repository(config):
    tempdir = tempfile.mkdtemp()
    for item in config:
        repo = item.get('git')
        ref = item.get('ref', 'master')
        fileoverlays = item.get('files', None)

        repodirname = _fetch_git_repo(repo, ref)

        if not fileoverlays:
            _symlink_all_content(repodirname, tempdir)
        else:
            for fileoverlay in fileoverlays:
                src = fileoverlay.get('src', None)
                dst = fileoverlay.get('dst', None)

                _link_overlay_files(repodirname, src, tempdir, dst)

    return tempdir


def _parse_reponimous_file(filename):
    stream = open(filename, 'r')
    return yaml.load(stream)


def _make_path_absolute(path):
    if os.path.isabs(path):
        return path
    return os.path.join(os.getcwd(), path)


def install(args):
    config = None
    ret = 0
    try:
        config = _parse_reponimous_file(args.config)
    except Exception as e:
        print sys.stderr, \
            "Error parsing reponimous file '%s': %s" % (args.config, e)

    path = _make_path_absolute(args.path)
    merged_repo = _create_merged_repository(config)
    parentpath = os.path.dirname(path)
    if not os.path.exists(parentpath):
        os.makedirs(parentpath)

    if not os.path.exists(path):
        shutil.move(merged_repo, path)
        print "Reponimous path: %s" % path
    else:
        print >> sys.stderr, "'%s' directory already exists" % path
        ret = -1
    shutil.rmtree(merged_repo, ignore_errors=True)

    if not ret == 0:
        sys.exit(ret)


def archive(args):
    config = None
    try:
        config = _parse_reponimous_file(args.config)
    except Exception as e:
        print sys.stderr, \
            "Error parsing reponimous file '%s': %s" % (args.config, e)

    path = _make_path_absolute(args.path)
    merged_repo = _create_merged_repository(config)
    archivepath = _archive(merged_repo, args.name, path)
    print "Archived reponimous to %s" % archivepath
    shutil.rmtree(merged_repo, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser.add_argument('--config', type=str, default='Reponimous')

    parser_install = subparsers.add_parser('install')
    parser_install.add_argument('--path', type=str)
    parser_install.set_defaults(func=install)

    parser_archive = subparsers.add_parser('archive')
    parser_archive.add_argument('--path', type=str, default=os.getcwd())
    parser_archive.add_argument('--name', type=str, default="reponimous")
    parser_archive.set_defaults(func=archive)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
