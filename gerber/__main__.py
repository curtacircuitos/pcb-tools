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

import os
import argparse
from .render import available_renderers
from .render import theme
from .pcb import PCB
from . import load_layer


def main():
    parser = argparse.ArgumentParser(
        description='Render gerber files to image',
        prog='gerber-render'
    )
    parser.add_argument(
        'filenames', metavar='FILENAME', type=str, nargs='+',
        help='Gerber files to render. If a directory is provided, it should '
             'be provided alone and should contain the gerber files for a '
             'single PCB.'
    )
    parser.add_argument(
        '--outfile', '-o', type=str, nargs='?', default='out',
        help="Output Filename (extension will be added automatically)"
    )
    parser.add_argument(
        '--backend', '-b', choices=available_renderers.keys(), default='cairo',
        help='Choose the backend to use to generate the output.'
    )
    parser.add_argument(
        '--theme', '-t', choices=theme.THEMES.keys(), default='default',
        help='Select render theme.'
    )
    parser.add_argument(
        '--width', type=int, default=1920, help='Maximum width.'
    )
    parser.add_argument(
        '--height', type=int, default=1080, help='Maximum height.'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', default=False,
        help='Increase verbosity of the output.'
    )
    # parser.add_argument(
    #     '--quick', '-q', action='store_true', default=False,
    #     help='Skip longer running rendering steps to produce lower quality'
    #          ' output faster. This only has an effect for the freecad backend.'
    # )
    # parser.add_argument(
    #     '--nox', action='store_true', default=False,
    #     help='Run without using any GUI elements. This may produce suboptimal'
    #          'output. For the freecad backend, colors, transparancy, and '
    #          'visibility cannot be set without a GUI instance.'
    # )

    args = parser.parse_args()

    renderer = available_renderers[args.backend]()

    if args.backend in ['cairo', ]:
        outext = 'png'
    else:
        outext = None

    if os.path.exists(args.filenames[0]) and os.path.isdir(args.filenames[0]):
        directory = args.filenames[0]
        pcb = PCB.from_directory(directory)

        if args.backend in ['cairo', ]:
            top = pcb.top_layers
            bottom = pcb.bottom_layers
            copper = pcb.copper_layers

            outline = pcb.outline_layer
            if outline:
                top = [outline] + top
                bottom = [outline] + bottom
                copper = [outline] + copper + pcb.drill_layers

            renderer.render_layers(
                layers=top, theme=theme.THEMES[args.theme],
                max_height=args.height, max_width=args.width,
                filename='{0}.top.{1}'.format(args.outfile, outext)
            )
            renderer.render_layers(
                layers=bottom, theme=theme.THEMES[args.theme],
                max_height=args.height, max_width=args.width,
                filename='{0}.bottom.{1}'.format(args.outfile, outext)
            )
            renderer.render_layers(
                layers=copper, theme=theme.THEMES['Transparent Multilayer'],
                max_height=args.height, max_width=args.width,
                filename='{0}.copper.{1}'.format(args.outfile, outext))
        else:
            pass
    else:
        filenames = args.filenames
        for filename in filenames:
            layer = load_layer(filename)
            settings = theme.THEMES[args.theme].get(layer.layer_class, None)
            renderer.render_layer(layer, settings=settings)
        renderer.dump(filename='{0}.{1}'.format(args.outfile, outext))


if __name__ == '__main__':
    main()

