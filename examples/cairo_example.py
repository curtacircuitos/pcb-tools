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
from gerber import load_layer
from gerber.render import RenderSettings, theme
from gerber.render.cairo_backend import GerberCairoContext

GERBER_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'gerbers'))


# Open the gerber files
copper = load_layer(os.path.join(GERBER_FOLDER, 'copper.GTL'))
mask = load_layer(os.path.join(GERBER_FOLDER, 'soldermask.GTS'))
silk = load_layer(os.path.join(GERBER_FOLDER, 'silkscreen.GTO'))
drill = load_layer(os.path.join(GERBER_FOLDER, 'ncdrill.DRD'))

# Create a new drawing context
ctx = GerberCairoContext()

# Draw the copper layer. render_layer() uses the default color scheme for the
# layer, based on the layer type. Copper layers are rendered as
ctx.render_layer(copper)

# Draw the soldermask layer
ctx.render_layer(mask)


# The default style can be overridden by passing a RenderSettings instance to
# render_layer().
# First, create a settings object:
our_settings = RenderSettings(color=theme.COLORS['white'], alpha=0.85)

# Draw the silkscreen layer, and specify the rendering settings to use
ctx.render_layer(silk, settings=our_settings)

# Draw the drill layer
ctx.render_layer(drill)

# Write output to png file
ctx.dump(os.path.join(os.path.dirname(__file__), 'cairo_example.png'))

# Load the bottom layers
copper = load_layer(os.path.join(GERBER_FOLDER, 'bottom_copper.GBL'))
mask = load_layer(os.path.join(GERBER_FOLDER, 'bottom_mask.GBS'))

# Clear the drawing
ctx.clear()

# Render bottom layers
ctx.render_layer(copper)
ctx.render_layer(mask)
ctx.render_layer(drill)

# Write png file
ctx.dump(os.path.join(os.path.dirname(__file__), 'cairo_bottom.png'))
