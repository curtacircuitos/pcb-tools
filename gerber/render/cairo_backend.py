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
import os
import tempfile
import copy

from .render import GerberContext, RenderSettings
from .theme import THEMES
from ..primitives import *

try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO


class GerberCairoContext(GerberContext):

    def __init__(self, scale=300):
        super(GerberCairoContext, self).__init__()
        self.scale = (scale, scale)
        self.surface = None
        self.surface_buffer = None
        self.ctx = None
        self.active_layer = None
        self.active_matrix = None
        self.output_ctx = None
        self.has_bg = False
        self.origin_in_inch = None
        self.size_in_inch = None
        self._xform_matrix = None
        self._render_count = 0

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
            self.surface = cairo.SVGSurface(self.surface_buffer, size_in_pixels[0], size_in_pixels[1])
            self.output_ctx = cairo.Context(self.surface)
            self.output_ctx.scale(1, -1)
            self.output_ctx.translate(-(origin_in_inch[0] * self.scale[0]),
                                      (-origin_in_inch[1] * self.scale[0]) - size_in_pixels[1])
        self._xform_matrix = cairo.Matrix(xx=1.0, yy=-1.0,
                                          x0=-self.origin_in_pixels[0],
                                          y0=self.size_in_pixels[1] + self.origin_in_pixels[1])

    def render_layer(self, layer, filename=None, settings=None, bgsettings=None,
                     verbose=False):
        if settings is None:
            settings = THEMES['default'].get(layer.layer_class, RenderSettings())
        if bgsettings is None:
            bgsettings = THEMES['default'].get('background', RenderSettings())

        if self._render_count == 0:
            if verbose:
                print('[Render]: Rendering Background.')
            self.clear()
            self.set_bounds(layer.bounds)
            self._paint_background(bgsettings)
        if verbose:
            print('[Render]: Rendering {} Layer.'.format(layer.layer_class))
        self._render_count += 1
        self._render_layer(layer, settings)
        if filename is not None:
            self.dump(filename, verbose)

    def render_layers(self, layers, filename, theme=THEMES['default'],
                      verbose=False):
        """ Render a set of layers
        """
        self.clear()
        bgsettings = theme['background']
        for layer in layers:
            settings = theme.get(layer.layer_class, RenderSettings())
            self.render_layer(layer, settings=settings, bgsettings=bgsettings,
                              verbose=verbose)
        self.dump(filename, verbose)

    def dump(self, filename, verbose=False):
        """ Save image as `filename`
        """
        is_svg = os.path.splitext(filename.lower())[1] == '.svg'
        if verbose:
            print('[Render]: Writing image to {}'.format(filename))
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

    def clear(self):
        self.surface = None
        self.output_ctx = None
        self.has_bg = False
        self.origin_in_inch = None
        self.size_in_inch = None
        self._xform_matrix = None
        self._render_count = 0
        if hasattr(self.surface_buffer, 'close'):
            self.surface_buffer.close()
            self.surface_buffer = None

    def _render_layer(self, layer, settings):
        self.invert = settings.invert
        # Get a new clean layer to render on
        self._new_render_layer(mirror=settings.mirror)
        for prim in layer.primitives:
            self.render(prim)
        # Add layer to image
        self._paint(settings.color, settings.alpha)

    def _render_line(self, line, color):
        start = [pos * scale for pos, scale in zip(line.start, self.scale)]
        end = [pos * scale for pos, scale in zip(line.end, self.scale)]
        self.ctx.set_operator(cairo.OPERATOR_SOURCE
                              if line.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
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
        width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        self.ctx.set_operator(cairo.OPERATOR_SOURCE
                              if arc.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(width * self.scale[0])
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            self.ctx.arc(*center, radius=radius, angle1=angle1, angle2=angle2)
        else:
            self.ctx.arc_negative(*center, radius=radius,
                                  angle1=angle1, angle2=angle2)
        self.ctx.move_to(*end)  # ...lame

    def _render_region(self, region, color):
        self.ctx.set_operator(cairo.OPERATOR_SOURCE
                              if region.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
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
        self.ctx.set_operator(cairo.OPERATOR_SOURCE
                              if circle.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(0)
        self.ctx.arc(*center, radius=(circle.radius * self.scale[0]), angle1=0,
                     angle2=(2 * math.pi))
        self.ctx.fill()

    def _render_rectangle(self, rectangle, color):
        lower_left = self.scale_point(rectangle.lower_left)
        width, height = tuple([abs(coord) for coord in
                               self.scale_point((rectangle.width,
                                                 rectangle.height))])
        self.ctx.set_operator(cairo.OPERATOR_SOURCE
                              if rectangle.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.set_line_width(0)
        self.ctx.rectangle(*lower_left, width=width, height=height)
        self.ctx.fill()

    def _render_obround(self, obround, color):
        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)

    def _render_drill(self, circle, color=None):
        color = color if color is not None else self.drill_color
        self._render_circle(circle, color)

    def _render_test_record(self, primitive, color):
        position = [pos + origin for pos, origin in
                    zip(primitive.position, self.origin_in_inch)]
        self.ctx.select_font_face(
            'monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.set_font_size(13)
        self._render_circle(Circle(position, 0.015), color)
        self.ctx.set_operator(cairo.OPERATOR_SOURCE
                              if primitive.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.move_to(*[self.scale[0] * (coord + 0.015) for coord in position])
        self.ctx.scale(1, -1)
        self.ctx.show_text(primitive.net_name)
        self.ctx.scale(1, -1)

    def _new_render_layer(self, color=None, mirror=False):
        size_in_pixels = self.scale_point(self.size_in_inch)
        matrix = copy.copy(self._xform_matrix)
        layer = cairo.SVGSurface(None, size_in_pixels[0], size_in_pixels[1])
        ctx = cairo.Context(layer)
        ctx.scale(1, -1)
        ctx.translate(-(self.origin_in_inch[0] * self.scale[0]),
                      (-self.origin_in_inch[1] * self.scale[0]) - size_in_pixels[1])
        if self.invert:
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.paint()
        if mirror:
            matrix.xx = -1.0
            matrix.x0 = self.origin_in_pixels[0] + self.size_in_pixels[0]
        self.ctx = ctx
        self.active_layer = layer
        self.active_matrix = matrix

    def _paint(self, color=None, alpha=None):
        color = color if color is not None else self.color
        alpha = alpha if alpha is not None else self.alpha
        ptn = cairo.SurfacePattern(self.active_layer)
        ptn.set_matrix(self.active_matrix)
        self.output_ctx.set_source_rgba(*color, alpha=alpha)
        self.output_ctx.mask(ptn)
        self.ctx = None
        self.active_layer = None
        self.active_matrix = None

    def _paint_background(self, settings=None):
        color = settings.color if settings is not None else self.background_color
        alpha = settings.alpha if settings is not None else 1.0
        if not self.has_bg:
            self.has_bg = True
            self.output_ctx.set_source_rgba(*color, alpha=alpha)
            self.output_ctx.paint()

    def scale_point(self, point):
        return tuple([coord * scale for coord, scale in zip(point, self.scale)])
