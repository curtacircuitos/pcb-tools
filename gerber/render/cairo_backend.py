#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .render import GerberContext
from .render import PCBContext

import cairocffi as cairo

from gerber.common import read
from operator import mul
import math
import tempfile
import os

from ..primitives import *


class GerberCairoContext(GerberContext):
    def __init__(self, scale=300):
        GerberContext.__init__(self)
        self.scale = (scale, scale)
        self.surface = None
        self.ctx = None
        self.bg = False

    def set_bounds(self, bounds):
        origin_in_inch = (bounds[0][0], bounds[1][0])
        size_in_inch = (abs(bounds[0][1] - bounds[0][0]), abs(bounds[1][1] - bounds[1][0]))
        size_in_pixels = map(mul, size_in_inch, self.scale)

        if self.surface is None:
            self.surface_buffer = tempfile.NamedTemporaryFile()
            self.surface = cairo.SVGSurface(self.surface_buffer, size_in_pixels[0], size_in_pixels[1])
            self.ctx = cairo.Context(self.surface)
            self.ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            self.ctx.scale(1, -1)
            self.ctx.translate(-(origin_in_inch[0] * self.scale[0]), (-origin_in_inch[1]*self.scale[0]) - size_in_pixels[1])
            # self.ctx.translate(-(origin_in_inch[0] * self.scale[0]), -origin_in_inch[1]*self.scale[1])

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter
            self.ctx.set_source_rgba(*color, alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER if (line.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
            self.ctx.set_line_width(width * self.scale[0])
            self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            self.ctx.move_to(*start)
            self.ctx.line_to(*end)
            self.ctx.stroke()
        elif isinstance(line.aperture, Rectangle):
            points = [tuple(map(mul, x, self.scale)) for x in line.vertices]
            self.ctx.set_source_rgba(*color, alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER if (line.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
            self.ctx.set_line_width(0)
            self.ctx.move_to(*points[0])
            for point in points[1:]:
                self.ctx.line_to(*point)
            self.ctx.fill()

    def _render_arc(self, arc, color):
        center = map(mul, arc.center, self.scale)
        start = map(mul, arc.start, self.scale)
        end = map(mul, arc.end, self.scale)
        radius = self.scale[0] * arc.radius
        angle1 = arc.start_angle
        angle2 = arc.end_angle
        width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_operator(cairo.OPERATOR_OVER if (arc.level_polarity == "dark" and not self.invert)else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(width * self.scale[0])
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            self.ctx.arc(*center, radius=radius, angle1=angle1, angle2=angle2)
        else:
            self.ctx.arc_negative(*center, radius=radius, angle1=angle1, angle2=angle2)
        self.ctx.move_to(*end)  # ...lame

    def _render_region(self, region, color):
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_operator(cairo.OPERATOR_OVER if (region.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(0)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*tuple(map(mul, region.primitives[0].start, self.scale)))
        for p in region.primitives:
            if isinstance(p, Line):
                self.ctx.line_to(*tuple(map(mul, p.end, self.scale)))
            else:
                center = map(mul, p.center, self.scale)
                start = map(mul, p.start, self.scale)
                end = map(mul, p.end, self.scale)
                radius = self.scale[0] * p.radius
                angle1 = p.start_angle
                angle2 = p.end_angle
                if p.direction == 'counterclockwise':
                    self.ctx.arc(*center, radius=radius, angle1=angle1, angle2=angle2)
                else:
                    self.ctx.arc_negative(*center, radius=radius, angle1=angle1, angle2=angle2)
        self.ctx.fill()

    def _render_circle(self, circle, color):
        center = tuple(map(mul, circle.position, self.scale))
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_operator(cairo.OPERATOR_OVER if (circle.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(0)
        self.ctx.arc(*center, radius=circle.radius * self.scale[0], angle1=0, angle2=2 * math.pi)
        self.ctx.fill()

    def _render_rectangle(self, rectangle, color):
        ll = map(mul, rectangle.lower_left, self.scale)
        width, height = tuple(map(mul, (rectangle.width, rectangle.height), map(abs, self.scale)))
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_operator(cairo.OPERATOR_OVER if (rectangle.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(0)
        self.ctx.rectangle(*ll,width=width, height=height)
        self.ctx.fill()

    def _render_obround(self, obround, color):
        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)

    def _render_drill(self, circle, color):
        self._render_circle(circle, color)

    def _render_test_record(self, primitive, color):
        self.ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.ctx.set_font_size(200)
        self._render_circle(Circle(primitive.position, 0.01), color)
        self.ctx.set_source_rgb(*color)
        self.ctx.set_operator(cairo.OPERATOR_OVER if (primitive.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.move_to(*[self.scale[0] * (coord + 0.01) for coord in primitive.position])
        self.ctx.scale(1, -1)
        self.ctx.show_text(primitive.net_name)
        self.ctx.scale(1, -1)

    def _paint_inverted_layer(self):
        self.ctx.set_source_rgba(*self.background_color)
        self.ctx.set_operator(cairo.OPERATOR_OVER)
        self.ctx.paint()
        self.ctx.set_operator(cairo.OPERATOR_CLEAR)

    def _paint_background(self):
        if not self.bg:
            self.bg = True
            self.ctx.set_source_rgba(*self.background_color)
            self.ctx.paint()

    def dump(self, filename):
        is_svg = filename.lower().endswith(".svg")

        if is_svg:
            self.surface.finish()
            self.surface_buffer.flush()

            with open(filename, "w") as f:
                self.surface_buffer.seek(0)
                f.write(self.surface_buffer.read())
                f.flush()

        else:
            self.surface.write_to_png(filename)

    def dump_svg_str(self):
        self.surface.finish()
        self.surface_buffer.flush()
        return self.surface_buffer.read()


class PCBCairoContext(PCBContext):
    def render(self, output_filename=None):
        if self.dialect:
            self.layers = self.dialect(self.filenames)
        ctx = GerberCairoContext()
        ctx.alpha = 0.95
        for filename in self.filenames:
            print("parsing %s" % filename)
            if filename in self.layers.outer_copper_layers:
                ctx.color = (1, 1, 1)
                ctx.alpha = 0.8
            elif filename in self.layers.silk_layers:
                ctx.color = (0.2, 0.2, 0.75)
                ctx.alpha = 0.8
            gerberfile = read(filename)
            gerberfile.render(ctx)
        if not output_filename:
            output_filename = self.layers.pcbname
        if os.path.splitext(output_filename)[1].upper() != 'SVG':
            output_filename += '.svg'
        print('Saving image to {0}'.format(output_filename))
        ctx.dump(output_filename)
