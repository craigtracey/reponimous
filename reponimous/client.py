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
import git
import glob
import os
import re
import shutil
import sys
import tarfile
import tempfile
import yaml


def _fetch_git_repo(repo, ref):

    home = os.path.expanduser("~")
    reponimousdir = os.path.join(home, ".reponimous")
    if not os.path.isdir(reponimousdir):
        os.makedirs(reponimousdir)

    reponame = os.path.basename(repo)
    reponame = re.sub(".git$", '', reponame)

    repodirname = os.path.join(reponimousdir, "%s-%s" % (reponame, ref))

    gitrepo = None
    if not os.path.isdir(repodirname):
        gitrepo = git.Git().clone(repo, repodirname)

    gitrepo = git.Repo(repodirname)
    origin = gitrepo.remotes.origin

    gitrepo.git.checkout(ref)
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
        srcbase = dirname[len(src)+1:]
        dstbase = os.path.join(dst, dirname[len(src)+1:])
        for subdir in subdirs:
            if subdir.startswith('.git'):
                continue
            os.makedirs(os.path.join(dstbase, subdir))
        for filename in filenames:
            if filename.startswith('.git'):
                continue
            os.symlink(os.path.join(src, srcbase, filename),
                       os.path.join(dstbase, dirname[len(src)+1:1], filename))


def _link_overlay_files(srcdir, src, dstdir, dst):
    srcfiles = glob.glob(os.path.join(srcdir, src))

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
                filedstdir = os.path.join(dstdir,
                                          os.path.dirname(filename)[len(srcdir)+1:])
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
                linkdstdir = os.path.join(dstdir, dst, os.path.basename(filename))
                _force_symlink(filename, linkdstdir)
                continue

            if not dst:
                linkdstdir = os.path.join(dstdir,
                                          os.path.dirname(filename)[len(srcdir)+1:])
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
        archivename = name

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


def _create_merged_repository(config, archive=False, path=None):

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

    if archive:
        archivepath = _archive(tempdir)
        print "Archived reponimous to %s" % archivepath
    elif path:
        pathparent = os.path.dirname(path)
        if not pathparent =='' and not os.path.exists(pathparent):
            os.makedirs(os.path.dirname(pathparent))

        if not os.path.exists(path):
            shutil.move(tempdir, path)
            print "Reponimous path: %s" % path
        else:
            print >> sys.stderr, "--path directory already exists"
            sys.exit(-1)

    shutil.rmtree(tempdir, ignore_errors=True)


def _parse_reponimous_file(filename):
    stream = open(filename, 'r')
    return yaml.load(stream)


def install(args):
    filename = args.config

    if not os.path.isfile(filename):
        print >> sys.stderr, "Reponimous file not found"
        sys.exit(-1)

    if not args.archive and not args.path:
        print >> sys.stderr, "You must provide either --path or --archive"
        sys.exit(-1)

    config = None
    try:
        config = _parse_reponimous_file(filename)
    except Exception as e:
        print "ERROR: Error parsing reponimous file '%s': %s" % (config, e)

    _create_merged_repository(config, args.archive, args.path)

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_install = subparsers.add_parser('install')
    parser_install.add_argument('--config', type=str, default='Reponimous')
    parser_install.add_argument('--path', type=str)
    parser_install.add_argument('--archive', type=str)
    parser_install.set_defaults(func=install)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
