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


import cairocffi as cairo
from operator import mul, div
import math
import tempfile

from .render import GerberContext
from ..primitives import *

try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO


class GerberCairoContext(GerberContext):
    def __init__(self, scale=300):
        GerberContext.__init__(self)
        self.scale = (scale, scale)
        self.surface = None
        self.ctx = None
        self.bg = False
        self.mask = None
        self.mask_ctx = None
        self.origin_in_inch = None
        self.size_in_inch = None

    def set_bounds(self, bounds, new_surface=False):
        origin_in_inch = (bounds[0][0], bounds[1][0])
        size_in_inch = (abs(bounds[0][1] - bounds[0][0]), abs(bounds[1][1] - bounds[1][0]))
        size_in_pixels = map(mul, size_in_inch, self.scale)
        self.origin_in_inch = origin_in_inch if self.origin_in_inch is None else self.origin_in_inch
        self.size_in_inch = size_in_inch if self.size_in_inch is None else self.size_in_inch
        if (self.surface is None) or new_surface:
            self.surface_buffer = tempfile.NamedTemporaryFile()
            self.surface = cairo.SVGSurface(self.surface_buffer, size_in_pixels[0], size_in_pixels[1])
            self.ctx = cairo.Context(self.surface)
            self.ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            self.ctx.scale(1, -1)
            self.ctx.translate(-(origin_in_inch[0] * self.scale[0]), (-origin_in_inch[1]*self.scale[0]) - size_in_pixels[1])
            self.mask = cairo.SVGSurface(None, size_in_pixels[0], size_in_pixels[1])
            self.mask_ctx = cairo.Context(self.mask)
            self.mask_ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            self.mask_ctx.scale(1, -1)
            self.mask_ctx.translate(-(origin_in_inch[0] * self.scale[0]), (-origin_in_inch[1]*self.scale[0]) - size_in_pixels[1])

    def render_layers(self, layers, filename):
        """ Render a set of layers
        """
        self.set_bounds(layers[0].bounds, True)
        self._paint_background(True)
        for layer in layers:
            self._render_layer(layer)
        self.dump(filename)

    @property
    def origin_in_pixels(self):
        return tuple(map(mul, self.origin_in_inch, self.scale)) if self.origin_in_inch is not None else (0.0, 0.0)

    @property
    def size_in_pixels(self):
        return tuple(map(mul, self.size_in_inch, self.scale)) if self.size_in_inch is not None else (0.0, 0.0)

    def _render_layer(self, layer):
        self.color = layer.settings.color
        self.alpha = layer.settings.alpha
        self.invert = layer.settings.invert
        if layer.settings.mirror:
            raise Warning('mirrored layers aren\'t supported yet...')
        if self.invert:
            self._clear_mask()
        for p in layer.primitives:
            self.render(p)
        if self.invert:
            self._render_mask()

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(*color, alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if line.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter
            ctx.set_line_width(width * self.scale[0])
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(*start)
            ctx.line_to(*end)
            ctx.stroke()
        elif isinstance(line.aperture, Rectangle):
            points = [tuple(map(mul, x, self.scale)) for x in line.vertices]
            ctx.set_line_width(0)
            ctx.move_to(*points[0])
            for point in points[1:]:
                ctx.line_to(*point)
            ctx.fill()

    def _render_arc(self, arc, color):
        center = map(mul, arc.center, self.scale)
        start = map(mul, arc.start, self.scale)
        end = map(mul, arc.end, self.scale)
        radius = self.scale[0] * arc.radius
        angle1 = arc.start_angle
        angle2 = arc.end_angle
        width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(*color, alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if arc.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.set_line_width(width * self.scale[0])
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            ctx.arc(*center, radius=radius, angle1=angle1, angle2=angle2)
        else:
            ctx.arc_negative(*center, radius=radius, angle1=angle1, angle2=angle2)
        ctx.move_to(*end)  # ...lame

    def _render_region(self, region, color):
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(*color, alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if region.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.set_line_width(0)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(*tuple(map(mul, region.primitives[0].start, self.scale)))
        for p in region.primitives:
            if isinstance(p, Line):
                ctx.line_to(*tuple(map(mul, p.end, self.scale)))
            else:
                center = map(mul, p.center, self.scale)
                start = map(mul, p.start, self.scale)
                end = map(mul, p.end, self.scale)
                radius = self.scale[0] * p.radius
                angle1 = p.start_angle
                angle2 = p.end_angle
                if p.direction == 'counterclockwise':
                    ctx.arc(*center, radius=radius, angle1=angle1, angle2=angle2)
                else:
                    ctx.arc_negative(*center, radius=radius, angle1=angle1, angle2=angle2)
        ctx.fill()

    def _render_circle(self, circle, color):
        center = tuple(map(mul, circle.position, self.scale))
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(*color, alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if circle.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.set_line_width(0)
        ctx.arc(*center, radius=circle.radius * self.scale[0], angle1=0, angle2=2 * math.pi)
        ctx.fill()

    def _render_rectangle(self, rectangle, color):
        ll = map(mul, rectangle.lower_left, self.scale)
        width, height = tuple(map(mul, (rectangle.width, rectangle.height), map(abs, self.scale)))
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(*color, alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if rectangle.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.set_line_width(0)
        ctx.rectangle(*ll, width=width, height=height)
        ctx.fill()

    def _render_obround(self, obround, color):
        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)

    def _render_drill(self, circle, color):
        self._render_circle(circle, color)

    def _render_test_record(self, primitive, color):
        position = tuple(map(add, primitive.position, self.origin_in_inch))
        self.ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.set_font_size(13)
        self._render_circle(Circle(position, 0.015), color)
        self.ctx.set_source_rgb(*color)
        self.ctx.set_operator(cairo.OPERATOR_OVER if primitive.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        self.ctx.move_to(*[self.scale[0] * (coord + 0.015) for coord in position])
        self.ctx.scale(1, -1)
        self.ctx.show_text(primitive.net_name)
        self.ctx.scale(1, -1)

    def _clear_mask(self):
        self.mask_ctx.set_operator(cairo.OPERATOR_OVER)
        self.mask_ctx.set_source_rgba(*self.color, alpha=self.alpha)
        self.mask_ctx.paint()

    def _render_mask(self):
        self.ctx.set_operator(cairo.OPERATOR_OVER)
        ptn = cairo.SurfacePattern(self.mask)
        ptn.set_matrix(cairo.Matrix(xx=1.0, yy=-1.0, x0=-self.origin_in_pixels[0],
                                    y0=self.size_in_pixels[1] + self.origin_in_pixels[1]))
        self.ctx.set_source(ptn)
        self.ctx.paint()

    def _paint_background(self, force=False):
        if (not self.bg) or force:
            self.bg = True
            self.ctx.set_source_rgba(*self.background_color, alpha=1.0)
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

    def dump_str(self):
        """ Return a string containing the rendered image.
        """
        fobj = StringIO()
        self.surface.write_to_png(fobj)
        return fobj.getvalue()

    def dump_svg_str(self):
        """ Return a string containg the rendered SVG.
        """
        self.surface.finish()
        self.surface_buffer.flush()
        return self.surface_buffer.read()
