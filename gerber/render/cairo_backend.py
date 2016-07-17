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

try:
    import cairo
except ImportError:
    import cairocffi as cairo

from operator import mul
import math
import tempfile

from ..primitives import *


class GerberCairoContext(GerberContext):
    def __init__(self, scale=300):
        GerberContext.__init__(self)
        self.scale = (scale, scale)
        self.surface = None
        self.ctx = None
        self.bg = False
        self.mask = None
        self.mask_ctx = None
        self.origin_in_pixels = None
        self.size_in_pixels = None

    def set_bounds(self, bounds):
        origin_in_inch = (bounds[0][0], bounds[1][0])
        size_in_inch = (abs(bounds[0][1] - bounds[0][0]), abs(bounds[1][1] - bounds[1][0]))
        size_in_pixels = map(mul, size_in_inch, self.scale)
        self.origin_in_pixels = tuple(map(mul, origin_in_inch, self.scale)) if self.origin_in_pixels is None else self.origin_in_pixels
        self.size_in_pixels = size_in_pixels if self.size_in_pixels is None else self.size_in_pixels
        if self.surface is None:
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

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
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
        if angle1 == angle2 and arc.quadrant_mode != 'single-quadrant':
            # Make the angles slightly different otherwise Cario will draw nothing
            angle2 -= 0.000000001
        if isinstance(arc.aperture, Circle):
            width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        else:
            width = max(arc.aperture.width, arc.aperture.height, 0.001)
        
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if arc.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
                
        ctx.set_line_width(width * self.scale[0])
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            ctx.arc(center[0], center[1], radius, angle1, angle2)
        else:
            ctx.arc_negative(center[0], center[1], radius, angle1, angle2)
        ctx.move_to(*end)  # ...lame
        ctx.stroke()

    def _render_region(self, region, color):
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
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
                    ctx.arc(center[0], center[1], radius, angle1, angle2)
                else:
                    ctx.arc_negative(center[0], center[1], radius, angle1, angle2)
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
        ctx.arc(center[0], center[1], radius=circle.radius * self.scale[0], angle1=0, angle2=2 * math.pi)
        ctx.fill()

    def _render_rectangle(self, rectangle, color):
        ll = map(mul, rectangle.lower_left, self.scale)
        width, height = tuple(map(mul, (rectangle.width, rectangle.height), map(abs, self.scale)))
        
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if rectangle.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
            
        if rectangle.rotation != 0:
            ctx.save()
            
            center = map(mul, rectangle.position, self.scale)
            matrix = cairo.Matrix()
            matrix.translate(center[0], center[1])
            # For drawing, we already handles the translation
            ll[0] = ll[0] - center[0]
            ll[1] = ll[1] - center[1]
            matrix.rotate(rectangle.rotation)
            ctx.transform(matrix)
     
        ctx.set_line_width(0)
        ctx.rectangle(ll[0], ll[1], width, height)
        ctx.fill()
        
        if rectangle.rotation != 0:
            ctx.restore()

    def _render_obround(self, obround, color):
        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)
        
    def _render_polygon(self, polygon, color):
        if polygon.hole_radius > 0:
            self.ctx.push_group()
        
        vertices = polygon.vertices 
        
        self.ctx.set_source_rgba(color[0], color[1], color[2], self.alpha)
        self.ctx.set_operator(cairo.OPERATOR_OVER if (polygon.level_polarity == "dark" and not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(0)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        
        # Start from before the end so it is easy to iterate and make sure it is closed
        self.ctx.move_to(*map(mul, vertices[-1], self.scale))
        for v in vertices:
            self.ctx.line_to(*map(mul, v, self.scale))

        self.ctx.fill()
        
        if polygon.hole_radius > 0:
            # Render the center clear
            center = tuple(map(mul, polygon.position, self.scale))
            self.ctx.set_source_rgba(color[0], color[1], color[2], self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)        
            self.ctx.set_line_width(0)
            self.ctx.arc(center[0], center[1], polygon.hole_radius * self.scale[0], 0, 2 * math.pi)
            self.ctx.fill()
            
            self.ctx.pop_group_to_source()
            self.ctx.paint_with_alpha(1)

    def _render_drill(self, circle, color):
        self._render_circle(circle, color)
        
    def _render_slot(self, slot, color):
        start = map(mul, slot.start, self.scale)
        end = map(mul, slot.end, self.scale)
        
        width = slot.diameter
        
        if not self.invert:
            ctx = self.ctx
            ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            ctx.set_operator(cairo.OPERATOR_OVER if slot.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            ctx = self.mask_ctx
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_CLEAR)

        ctx.set_line_width(width * self.scale[0])
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(*start)
        ctx.line_to(*end)
        ctx.stroke()
        
    def _render_amgroup(self, amgroup, color):
        self.ctx.push_group()
        for primitive in amgroup.primitives:
            self.render(primitive)
        self.ctx.pop_group_to_source()
        self.ctx.paint_with_alpha(1)

    def _render_test_record(self, primitive, color):
        self.ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.ctx.set_font_size(200)
        self._render_circle(Circle(primitive.position, 0.01), color)
        self.ctx.set_source_rgb(*color)
        self.ctx.set_operator(cairo.OPERATOR_OVER if primitive.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        self.ctx.move_to(*[self.scale[0] * (coord + 0.01) for coord in primitive.position])
        self.ctx.scale(1, -1)
        self.ctx.show_text(primitive.net_name)
        self.ctx.scale(1, -1)

    def _paint_inverted_layer(self):
        self.mask_ctx.set_operator(cairo.OPERATOR_OVER)
        self.mask_ctx.set_source_rgba(self.background_color[0], self.background_color[1], self.background_color[2], alpha=self.alpha)
        self.mask_ctx.paint()

    def _render_mask(self):
        self.ctx.set_operator(cairo.OPERATOR_OVER)
        ptn = cairo.SurfacePattern(self.mask)
        ptn.set_matrix(cairo.Matrix(xx=1.0, yy=-1.0, x0=-self.origin_in_pixels[0], y0=self.size_in_pixels[1] + self.origin_in_pixels[1]))
        self.ctx.set_source(ptn)
        self.ctx.paint()

    def _paint_background(self):
        if not self.bg:
            self.bg = True
            self.ctx.set_source_rgba(self.background_color[0], self.background_color[1], self.background_color[2])
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
