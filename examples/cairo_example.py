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
This example demonstrates the use of pcb-tools with cairo to render a composite
image from a set of gerber files. Each layer is loaded and drawn using a
GerberCairoContext. The color and opacity of each layer can be set individually.
Once all thedesired layers are drawn on the context, the context is written to
a .png file.
"""

import os
from gerber import read
from gerber.render import GerberCairoContext

GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))





# Open the gerber files
copper = read(os.path.join(GERBER_FOLDER, 'copper.GTL'))
mask = read(os.path.join(GERBER_FOLDER, 'soldermask.GTS'))
silk = read(os.path.join(GERBER_FOLDER, 'silkscreen.GTO'))
drill = read(os.path.join(GERBER_FOLDER, 'ncdrill.DRD'))


# Create a new drawing context
ctx = GerberCairoContext()

# Draw the copper layer
copper.render(ctx)

# Set opacity and color for soldermask layer
ctx.alpha = 0.6
ctx.color = (0.2, 0.2, 0.75)

# Draw the soldermask layer
mask.render(ctx)

# Set opacity and color for silkscreen layer
ctx.alpha = 0.85
ctx.color = (1, 1, 1)

# Draw the silkscreen layer
silk.render(ctx)

# Set opacity for drill layer
ctx.alpha = 1.
drill.render(ctx)

# Write output to png file
ctx.dump(os.path.join(os.path.dirname(__file__), 'cairo_example.png'))
