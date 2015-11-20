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
from .layers import available_dialects


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
        '--outfile', '-o', metavar='OUTFILE', type=str, nargs='?',
        default='test',
        help="Output Filename. Default 'test'. "
             "(extension will be added on automatically)"
    )
    parser.add_argument(
        '--backend', '-b', choices=['cairo', 'freecad'], default='cairo',
        help='Choose the backend to use to generate the output.'
             'cairo produces svg, freecad produces a 3d model.'
    )
    parser.add_argument(
        '--dialect', '-d', choices=available_dialects.keys(), default=None,
        help='Specify the dialect to use to guess layers from the filename.'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', default=False,
        help='Increase verbosity of the output.'
    )

    args = parser.parse_args()
    if args.dialect:
        if args.dialect in available_dialects.keys():
            dialect = available_dialects[args.dialect]
        else:
            raise ValueError('Unrecognized filename dialect ' + args.dialect)
    else:
        from layers import guess_dialect
        dialect = guess_dialect(args.filenames, verbose=args.verbose)

    if args.backend == 'cairo':
        from gerber.render import PCBCairoContext
        pcb_context = PCBCairoContext(args.filenames, dialect,
                                      verbose=args.verbose)
    elif args.backend == 'freecad':
        from gerber.render import PCBFreecadContext
        pcb_context = PCBFreecadContext(args.filenames, dialect,
                                        verbose=args.verbose)
    else:
        raise ValueError('Unrecognized backend ' + args.backend)

    pcb_context.render(output_filename=args.outfile)


if __name__ == '__main__':
    main()
