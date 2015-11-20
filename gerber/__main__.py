#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import argparse
from gerber.common import read


def render_cairo(filenames, dialect):
    from gerber.render import GerberCairoContext
    ctx = GerberCairoContext()
    ctx.alpha = 0.95
    for filename in filenames:
        print("parsing %s" % filename)
        if 'GTO' in filename or 'GBO' in filename:
            ctx.color = (1, 1, 1)
            ctx.alpha = 0.8
        elif 'GTS' in filename or 'GBS' in filename:
            ctx.color = (0.2, 0.2, 0.75)
            ctx.alpha = 0.8
        gerberfile = read(filename)
        gerberfile.render(ctx)

    print('Saving image to test.svg')
    ctx.dump('test.svg')


def render_freecad(filenames, dialect):
    try:
        from gerber.render import GerberFreecadContext
    except ImportError:
        print("Problem importing the Freecad context. Make sure you have "
              "FreeCAD installed and available on your python path.")
        raise
    pass


def main():
    parser = argparse.ArgumentParser(
        description='Render gerber files to image',
        prog='python -m gerber'
    )
    parser.add_argument(
        'filenames', metavar='FILENAME', type=str, nargs='+',
        help='Gerber files'
    )
    parser.add_argument(
        '--backend', '-b', choices=['cairo', 'freecad'], default='cairo',
        help='Choose the backend to use to generate the output.'
             'cairo produces svg, freecad produces a 3d model.'
    )
    parser.add_argument(
        '--dialect', '-d', choices=['geda'], default=None,
        help='Specify the dialect to use to guess layers from the filename'
    )

    args = parser.parse_args()
    if args.dialect:
        if args.dialect == 'geda':
            from layers import GedaGerberLayerDialect
            dialect = GedaGerberLayerDialect
        else:
            raise ValueError('Unknown filename dialect ' + args.dialect)
    else:
        dialect = None

    if args.backend == 'cairo':
        render_cairo(args.filenames, dialect)
    if args.backend == 'freecad':
        render_freecad(args.filenames, dialect)


if __name__ == '__main__':
    main()
