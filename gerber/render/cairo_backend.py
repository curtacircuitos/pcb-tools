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

try:
    import cairo
except ImportError:
    import cairocffi as cairo

import math
from operator import mul, div
import tempfile

import cairocffi as cairo

from ..primitives import *
from .render import GerberContext, RenderSettings
from .theme import THEMES

try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO


class GerberCairoContext(GerberContext):

    def __init__(self, scale=300):
        super(GerberCairoContext, self).__init__()
        self.scale = (scale, scale)
        self.surface = None
        self.ctx = None
        self.active_layer = None
        self.output_ctx = None
        self.bg = False
        self.mask = None
        self.mask_ctx = None
        self.origin_in_inch = None
        self.size_in_inch = None
        self._xform_matrix = None

    @property
    def origin_in_pixels(self):
        return (self.scale_point(self.origin_in_inch)
                if self.origin_in_inch is not None else (0.0, 0.0))

    @property
    def size_in_pixels(self):
        return (self.scale_point(self.size_in_inch)
                if self.size_in_inch is not None else (0.0, 0.0))

    def set_bounds(self, bounds, new_surface=False):
        origin_in_inch = (bounds[0][0], bounds[1][0])
        size_in_inch = (abs(bounds[0][1] - bounds[0][0]),
                        abs(bounds[1][1] - bounds[1][0]))
        size_in_pixels = self.scale_point(size_in_inch)
        self.origin_in_inch = origin_in_inch if self.origin_in_inch is None else self.origin_in_inch
        self.size_in_inch = size_in_inch if self.size_in_inch is None else self.size_in_inch
        if (self.surface is None) or new_surface:
            self.surface_buffer = tempfile.NamedTemporaryFile()
            self.surface = cairo.SVGSurface(
                self.surface_buffer, size_in_pixels[0], size_in_pixels[1])
            self.output_ctx = cairo.Context(self.surface)
            self.output_ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
            self.output_ctx.scale(1, -1)
            self.output_ctx.translate(-(origin_in_inch[0] * self.scale[0]),
                                      (-origin_in_inch[1] * self.scale[0]) - size_in_pixels[1])
        self._xform_matrix = cairo.Matrix(xx=1.0, yy=-1.0,
                                          x0=-self.origin_in_pixels[0],
                                          y0=self.size_in_pixels[1] + self.origin_in_pixels[1])

    def render_layers(self, layers, filename, theme=THEMES['default']):
        """ Render a set of layers
        """
        self.set_bounds(layers[0].bounds, True)
        self._paint_background(True)

        for layer in layers:
            self._render_layer(layer, theme)
        self.dump(filename)

    def dump(self, filename):
        """ Save image as `filename`
        """
        if filename and filename.lower().endswith(".svg"):
            self.surface.finish()
            self.surface_buffer.flush()
            with open(filename, "w") as f:
                self.surface_buffer.seek(0)
                f.write(self.surface_buffer.read())
                f.flush()
        else:
            return self.surface.write_to_png(filename)

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

    def _render_layer(self, layer, theme=THEMES['default']):
        settings = theme.get(layer.layer_class, RenderSettings())
        self.color = settings.color
        self.alpha = settings.alpha
        self.invert = settings.invert

        # Get a new clean layer to render on
        self._new_render_layer()
        if settings.mirror:
            raise Warning('mirrored layers aren\'t supported yet...')
        for prim in layer.primitives:
            self.render(prim)
        # Add layer to image
        self._flatten()

    def _render_line(self, line, color):
        start = [pos * scale for pos, scale in zip(line.start, self.scale)]
        end = [pos * scale for pos, scale in zip(line.end, self.scale)]
        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER
                             if line.level_polarity == "dark"
                             else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter
            self.ctx.set_line_width(width * self.scale[0])
            self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            self.ctx.move_to(*start)
            self.ctx.line_to(*end)
            self.ctx.stroke()
        elif isinstance(line.aperture, Rectangle):
            points = [self.scale_point(x) for x in line.vertices]
            self.ctx.set_line_width(0)
            self.ctx.move_to(*points[0])
            for point in points[1:]:
                self.ctx.line_to(*point)
            self.ctx.fill()

    def _render_arc(self, arc, color):
        center = self.scale_point(arc.center)
        start = self.scale_point(arc.start)
        end = self.scale_point(arc.end)
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
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER
                             if arc.level_polarity == "dark"\
                             else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        self.ctx.set_line_width(width * self.scale[0])
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            self.ctx.arc(center[0], center[1], radius, angle1, angle2)
        else:
            self.ctx.arc_negative(center[0], center[1], radius, angle1, angle2)
        self.ctx.move_to(*end)  # ...lame

    def _render_region(self, region, color):
        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER
                                  if region.level_polarity == "dark"
                                  else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        self.ctx.set_line_width(0)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*self.scale_point(region.primitives[0].start))
        for prim in region.primitives:
            if isinstance(prim, Line):
                self.ctx.line_to(*self.scale_point(prim.end))
            else:
                center = self.scale_point(prim.center)
                radius = self.scale[0] * prim.radius
                angle1 = prim.start_angle
                angle2 = prim.end_angle
                if prim.direction == 'counterclockwise':
                    self.ctx.arc(*center, radius=radius,
                                 angle1=angle1, angle2=angle2)
                else:
                    self.ctx.arc_negative(*center, radius=radius,
                                          angle1=angle1, angle2=angle2)

        self.ctx.fill()

    def _render_circle(self, circle, color):
        center = self.scale_point(circle.position)
        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER
                                  if circle.level_polarity == "dark"
                                  else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        if circle.hole_diameter > 0:
            self.ctx.push_group()

        self.ctx.set_line_width(0)
        self.ctx.arc(center[0], center[1], radius=circle.radius * self.scale[0], angle1=0, angle2=2 * math.pi)
        self.ctx.fill()

        if circle.hole_diameter > 0:
            # Render the center clear

            self.ctx.set_source_rgba(color[0], color[1], color[2], self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
            self.ctx.arc(center[0], center[1], radius=circle.hole_radius * self.scale[0], angle1=0, angle2=2 * math.pi)
            self.ctx.fill()

            self.ctx.pop_group_to_source()
            self.ctx.paint_with_alpha(1)

    def _render_rectangle(self, rectangle, color):
        lower_left = self.scale_point(rectangle.lower_left)
        width, height = tuple([abs(coord) for coord in self.scale_point((rectangle.width, rectangle.height))])


        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER
                             if rectangle.level_polarity == "dark"
                             else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        if rectangle.rotation != 0:
            self.ctx.save()

            center = map(mul, rectangle.position, self.scale)
            matrix = cairo.Matrix()
            matrix.translate(center[0], center[1])
            # For drawing, we already handles the translation
            lower_left[0] = lower_left[0] - center[0]
            lower_left[1] = lower_left[1] - center[1]
            matrix.rotate(rectangle.rotation)
            self.ctx.transform(matrix)

        if rectangle.hole_diameter > 0:
            self.ctx.push_group()

        self.ctx.set_line_width(0)
        self.ctx.rectangle(lower_left[0], lower_left[1], width, height)
        self.ctx.fill()

        if rectangle.hole_diameter > 0:
            # Render the center clear
            self.ctx.set_source_rgba(color[0], color[1], color[2], self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
            center = map(mul, rectangle.position, self.scale)
            self.ctx.arc(center[0], center[1], radius=rectangle.hole_radius * self.scale[0], angle1=0, angle2=2 * math.pi)
            self.ctx.fill()

            self.ctx.pop_group_to_source()
            self.ctx.paint_with_alpha(1)

        if rectangle.rotation != 0:
            self.ctx.restore()


    def _render_obround(self, obround, color):

        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER if obround.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        if obround.hole_diameter > 0:
            self.ctx.push_group()

        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)

        if obround.hole_diameter > 0:
            # Render the center clear
            self.ctx.set_source_rgba(color[0], color[1], color[2], self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
            center = map(mul, obround.position, self.scale)
            self.ctx.arc(center[0], center[1], radius=obround.hole_radius * self.scale[0], angle1=0, angle2=2 * math.pi)
            self.ctx.fill()

            self.ctx.pop_group_to_source()
            self.ctx.paint_with_alpha(1)

    def _render_polygon(self, polygon, color):

        # TODO Ths does not handle rotation of a polygon
        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER if polygon.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        if polygon.hole_radius > 0:
            self.ctx.push_group()

        vertices = polygon.vertices

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

    def _render_drill(self, circle, color=None):
        color = color if color is not None else self.drill_color
        self._render_circle(circle, color)

    def _render_slot(self, slot, color):
        start = map(mul, slot.start, self.scale)
        end = map(mul, slot.end, self.scale)

        width = slot.diameter

        if not self.invert:
            self.ctx.set_source_rgba(color[0], color[1], color[2], alpha=self.alpha)
            self.ctx.set_operator(cairo.OPERATOR_OVER if slot.level_polarity == "dark" else cairo.OPERATOR_CLEAR)
        else:
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)

        self.ctx.set_line_width(width * self.scale[0])
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*start)
        self.ctx.line_to(*end)
        self.ctx.stroke()

    def _render_amgroup(self, amgroup, color):
        self.ctx.push_group()
        for primitive in amgroup.primitives:
            self.render(primitive)
        self.ctx.pop_group_to_source()
        self.ctx.paint_with_alpha(1)

    def _render_test_record(self, primitive, color):
        position = [pos + origin for pos, origin in zip(primitive.position, self.origin_in_inch)]
        self.ctx.set_operator(cairo.OPERATOR_OVER)
        self.ctx.select_font_face(
            'monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.set_font_size(13)
        self._render_circle(Circle(position, 0.015), color)
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_operator(
            cairo.OPERATOR_OVER if primitive.level_polarity == 'dark' else cairo.OPERATOR_CLEAR)
        self.ctx.move_to(*[self.scale[0] * (coord + 0.015)
                           for coord in position])
        self.ctx.scale(1, -1)
        self.ctx.show_text(primitive.net_name)
        self.ctx.scale(1, -1)

    def _new_render_layer(self, color=None):
        size_in_pixels = self.scale_point(self.size_in_inch)
        layer = cairo.SVGSurface(None, size_in_pixels[0], size_in_pixels[1])
        ctx = cairo.Context(layer)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.scale(1, -1)
        ctx.translate(-(self.origin_in_inch[0] * self.scale[0]),
                           (-self.origin_in_inch[1] * self.scale[0])
                           - size_in_pixels[1])
        if self.invert:
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.set_source_rgba(*self.color, alpha=self.alpha)
            ctx.paint()
        self.ctx = ctx
        self.active_layer = layer

    def _flatten(self):
        self.output_ctx.set_operator(cairo.OPERATOR_OVER)
        ptn = cairo.SurfacePattern(self.active_layer)
        ptn.set_matrix(self._xform_matrix)
        self.output_ctx.set_source(ptn)
        self.output_ctx.paint()
        self.ctx = None
        self.active_layer = None

    def _paint_background(self, force=False):
        if (not self.bg) or force:
            self.bg = True
            self.output_ctx.set_operator(cairo.OPERATOR_OVER)
            self.output_ctx.set_source_rgba(self.background_color[0], self.background_color[1], self.background_color[2], alpha=1.0)
            self.output_ctx.paint()

    def scale_point(self, point):
        return tuple([coord * scale for coord, scale in zip(point, self.scale)])
