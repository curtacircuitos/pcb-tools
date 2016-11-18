#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Hamilton Kibbe <ham@hamiltonkib.be>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
This example renders the gerber files from the gerbv test suite
"""

import os
from gerber.rs274x import read as gerber_read
from gerber.excellon import read as excellon_read
from gerber.render import GerberCairoContext
from gerber.utils import listdir

GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbv_test_files'))

if not os.path.isdir(os.path.join(os.path.dirname(__file__), 'outputs')):
    os.mkdir(os.path.join(os.path.dirname(__file__), 'outputs'))

for infile in listdir(GERBER_FOLDER):
    if infile.startswith('test'):
        try:
            outfile = os.path.splitext(infile)[0] + '.png'
            if infile.endswith('gbx'):
                layer = gerber_read(os.path.join(GERBER_FOLDER, infile))
                print("Loaded Gerber file: {}".format(infile))
            elif infile.endswith('exc'):
                layer = excellon_read(os.path.join(GERBER_FOLDER, infile))
                print("Loaded Excellon file: {}".format(infile))
            else:
                continue

            # Create a new drawing context
            ctx = GerberCairoContext(1200)
            ctx.color = (80./255, 80/255., 154/255.)
            ctx.drill_color = ctx.color

            # Draw the layer, and specify the rendering settings to use
            layer.render(ctx)

            # Write output to png file
            print("Writing output to: {}".format(outfile))
            ctx.dump(os.path.join(os.path.dirname(__file__), 'outputs', outfile))
        except Exception as exc:
            import traceback
            traceback.print_exc()
