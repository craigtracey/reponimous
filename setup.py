#!/usr/bin/python
# Copyright (c) 2013 Blue Box Group, Inc.
# Copyright (c) 2013 Craig Tracey <craigtracey@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
try:
    from setuptools import setup, find_packages
    from setuptools.command.sdist import sdist
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    from setuptools.command.sdist import sdist

version_string = '0.0.1'

setup(
    name='reponimous',
    version=version_string,
    description='reponimous: a git overlay tool',
    license='Apache License (2.0)',
    author='Craig Tracey',
    author_email='craigtracey@gmail.com',
    url='http://scalehorizontally.com',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
    ],
    py_modules=[],
    entry_points = {
        'console_scripts': [
            'reponimous = reponimous.client:main'
        ]
    },
    install_requires = [
        'GitPython==0.3.2.RC1',
        'PyYAML',
        'giturlparse.py>=0.0.5'
    ],
)
