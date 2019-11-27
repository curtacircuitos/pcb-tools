#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


METADATA = {
    'name': 'pcb-tools',
    'version': 0.1,
    'author': 'Paulo Henrique Silva <ph.silva@gmail.com>, Hamilton Kibbe <ham@hamiltonkib.be>',
    'author_email': "ph.silva@gmail.com, ham@hamiltonkib.be",
    'description': "Utilities to handle Gerber (RS-274X) files.",
    'license': "Apache",
    'keywords': "pcb gerber tools",
    'url': "http://github.com/curtacircuitos/pcb-tools",
    'packages': ['gerber', 'gerber.render'],
    'long_description': read('README.md'),
    'classifiers': [
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apple Public Source License",
    ],
}

SETUPTOOLS_METADATA = {
    'install_requires': ['cairocffi==0.6'],
    'entry_points': {
        'console_scripts': [
            'gerber-render = gerber.__main__:main',
        ],
    },
}


def install():
    """ Install using setuptools, fallback to distutils
    """
    try:
        from setuptools import setup
        METADATA.update(SETUPTOOLS_METADATA)
        setup(**METADATA)
    except ImportError:
        from sys import stderr
        stderr.write('Could not import setuptools, using distutils')
        stderr.write('NOTE: You will need to install dependencies manually')
        from distutils.core import setup
        setup(**METADATA)


if __name__ == '__main__':
    install()
