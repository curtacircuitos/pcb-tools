#!/usr/bin/env python
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

from operator import mul
import tempfile
import copy
import os

from .render import GerberContext, RenderSettings
from .theme import THEMES
from ..primitives import *
from ..utils import rotate_point

from io import BytesIO


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
        self._xform_matrix = cairo.Matrix(xx=1.0, yy=-1.0,
                                          x0=-self.origin_in_pixels[0],
                                          y0=self.size_in_pixels[1])
        if (self.surface is None) or new_surface:
            self.surface_buffer = tempfile.NamedTemporaryFile()
            self.surface = cairo.SVGSurface(self.surface_buffer, size_in_pixels[0], size_in_pixels[1])
            self.output_ctx = cairo.Context(self.surface)

    def render_layer(self, layer, filename=None, settings=None, bgsettings=None,
                     verbose=False, bounds=None):
        if settings is None:
            settings = THEMES['default'].get(layer.layer_class, RenderSettings())
        if bgsettings is None:
            bgsettings = THEMES['default'].get('background', RenderSettings())

        if self._render_count == 0:
            if verbose:
                print('[Render]: Rendering Background.')
            self.clear()
            if bounds is not None:
                self.set_bounds(bounds)
            else:
                self.set_bounds(layer.bounds)
            self.paint_background(bgsettings)
        if verbose:
            print('[Render]: Rendering {} Layer.'.format(layer.layer_class))
        self._render_count += 1
        self._render_layer(layer, settings)
        if filename is not None:
            self.dump(filename, verbose)

    def render_layers(self, layers, filename, theme=THEMES['default'],
                      verbose=False, max_width=800, max_height=600):
        """ Render a set of layers
        """
        # Calculate scale parameter
        x_range = [10000, -10000]
        y_range = [10000, -10000]
        for layer in layers:
            bounds = layer.bounds
            if bounds is not None:
                layer_x, layer_y = bounds
                x_range[0] = min(x_range[0], layer_x[0])
                x_range[1] = max(x_range[1], layer_x[1])
                y_range[0] = min(y_range[0], layer_y[0])
                y_range[1] = max(y_range[1], layer_y[1])
        width = x_range[1] - x_range[0]
        height = y_range[1] - y_range[0]

        scale = math.floor(min(float(max_width)/width, float(max_height)/height))
        self.scale = (scale, scale)

        self.clear()

        # Render layers
        bgsettings = theme['background']
        for layer in layers:
            settings = theme.get(layer.layer_class, RenderSettings())
            self.render_layer(layer, settings=settings, bgsettings=bgsettings,
                              verbose=verbose)
        self.dump(filename, verbose)

    def dump(self, filename=None, verbose=False):
        """ Save image as `filename`
        """
        try:
            is_svg = os.path.splitext(filename.lower())[1] == '.svg'
        except:
            is_svg = False
        if verbose:
            print('[Render]: Writing image to {}'.format(filename))
        if is_svg:
            self.surface.finish()
            self.surface_buffer.flush()
            with open(filename, "wb") as f:
                self.surface_buffer.seek(0)
                f.write(self.surface_buffer.read())
                f.flush()
        else:
            return self.surface.write_to_png(filename)

    def dump_str(self):
        """ Return a byte-string containing the rendered image.
        """
        fobj = BytesIO()
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
        self.surface_buffer = None

    def _new_mask(self):
        class Mask:
            def __enter__(msk):
                size_in_pixels = self.size_in_pixels
                msk.surface = cairo.SVGSurface(None, size_in_pixels[0],
                                               size_in_pixels[1])
                msk.ctx = cairo.Context(msk.surface)
                msk.ctx.translate(-self.origin_in_pixels[0], -self.origin_in_pixels[1])
                return msk


            def __exit__(msk, exc_type, exc_val, traceback):
                if hasattr(msk.surface, 'finish'):
                    msk.surface.finish()

        return Mask()

    def _render_layer(self, layer, settings):
        self.invert = settings.invert
        # Get a new clean layer to render on
        self.new_render_layer(mirror=settings.mirror)
        for prim in layer.primitives:
            self.render(prim)
        # Add layer to image
        self.flatten(settings.color, settings.alpha)

    def _render_line(self, line, color):
        start = self.scale_point(line.start)
        end = self.scale_point(line.end)
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert)
                                 and line.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)

        with self._clip_primitive(line):
            with self._new_mask() as mask:
                if isinstance(line.aperture, Circle):
                    width = line.aperture.diameter
                    mask.ctx.set_line_width(width * self.scale[0])
                    mask.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                    mask.ctx.move_to(*start)
                    mask.ctx.line_to(*end)
                    mask.ctx.stroke()

                elif hasattr(line, 'vertices') and line.vertices is not None:
                    points = [self.scale_point(x) for x in line.vertices]
                    mask.ctx.set_line_width(0)
                    mask.ctx.move_to(*points[-1])
                    for point in points:
                        mask.ctx.line_to(*point)
                    mask.ctx.fill()
                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_arc(self, arc, color):
        center = self.scale_point(arc.center)
        start = self.scale_point(arc.start)
        end = self.scale_point(arc.end)
        radius = self.scale[0] * arc.radius
        two_pi = 2 * math.pi
        angle1 = (arc.start_angle + two_pi) % two_pi
        angle2 = (arc.end_angle + two_pi) % two_pi
        if angle1 == angle2 and arc.quadrant_mode != 'single-quadrant':
            # Make the angles slightly different otherwise Cario will draw nothing
            angle2 -= 0.000000001
        if isinstance(arc.aperture, Circle):
            width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        else:
            width = max(arc.aperture.width, arc.aperture.height, 0.001)

        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert)
                                 and arc.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(arc):
            with self._new_mask() as mask:
                mask.ctx.set_line_width(width * self.scale[0])
                mask.ctx.set_line_cap(cairo.LINE_CAP_ROUND if isinstance(arc.aperture, Circle) else cairo.LINE_CAP_SQUARE)
                mask.ctx.move_to(*start)  # You actually have to do this...
                if arc.direction == 'counterclockwise':
                    mask.ctx.arc(center[0], center[1], radius, angle1, angle2)
                else:
                    mask.ctx.arc_negative(center[0], center[1], radius,
                                          angle1, angle2)
                mask.ctx.move_to(*end)  # ...lame
                mask.ctx.stroke()

                #if isinstance(arc.aperture, Rectangle):
                #    print("Flash Rectangle Ends")
                #    print(arc.aperture.rotation * 180/math.pi)
                #    rect = arc.aperture
                #    width = self.scale[0] * rect.width
                #    height = self.scale[1] * rect.height
                #    for point, angle in zip((start, end), (angle1, angle2)):
                #        print("{} w {} h{}".format(point, rect.width, rect.height))
                #        mask.ctx.rectangle(point[0] - width/2.0,
                #                           point[1] - height/2.0, width, height)
                #        mask.ctx.fill()

                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_region(self, region, color):
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert) and region.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(region):
            with self._new_mask() as mask:
                mask.ctx.set_line_width(0)
                mask.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                mask.ctx.move_to(*self.scale_point(region.primitives[0].start))
                for prim in region.primitives:
                    if isinstance(prim, Line):
                        mask.ctx.line_to(*self.scale_point(prim.end))
                    else:
                        center = self.scale_point(prim.center)
                        radius = self.scale[0] * prim.radius
                        angle1 = prim.start_angle
                        angle2 = prim.end_angle
                        if prim.direction == 'counterclockwise':
                            mask.ctx.arc(center[0], center[1], radius,
                                         angle1, angle2)
                        else:
                            mask.ctx.arc_negative(center[0], center[1], radius,
                                                  angle1, angle2)
                mask.ctx.fill()
                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_circle(self, circle, color):
        center = self.scale_point(circle.position)
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert)
                                 and circle.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(circle):
            with self._new_mask() as mask:
                mask.ctx.set_line_width(0)
                mask.ctx.arc(center[0], center[1], (circle.radius * self.scale[0]), 0, (2 * math.pi))
                mask.ctx.fill()

                if hasattr(circle, 'hole_diameter') and circle.hole_diameter is not None and circle.hole_diameter > 0:
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR)
                    mask.ctx.arc(center[0], center[1], circle.hole_radius * self.scale[0], 0, 2 * math.pi)
                    mask.ctx.fill()

                if (hasattr(circle, 'hole_width') and hasattr(circle, 'hole_height')
                        and circle.hole_width is not None and circle.hole_height is not None
                        and circle.hole_width > 0 and circle.hole_height > 0):
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR
                                          if circle.level_polarity == 'dark'
                                             and (not self.invert)
                                          else cairo.OPERATOR_OVER)
                    width, height = self.scale_point((circle.hole_width, circle.hole_height))
                    lower_left = rotate_point(
                        (center[0] - width / 2.0, center[1] - height / 2.0),
                                              circle.rotation, center)
                    lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0),
                                               circle.rotation, center)
                    upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0),
                                              circle.rotation, center)
                    upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0),
                                               circle.rotation, center)
                    points = (lower_left, lower_right, upper_right, upper_left)
                    mask.ctx.move_to(*points[-1])
                    for point in points:
                        mask.ctx.line_to(*point)
                    mask.ctx.fill()
                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_rectangle(self, rectangle, color):
        lower_left = self.scale_point(rectangle.lower_left)
        width, height = tuple([abs(coord) for coord in
                               self.scale_point((rectangle.width,
                                                 rectangle.height))])
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert)
                                 and rectangle.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(rectangle):
            with self._new_mask() as mask:
                mask.ctx.set_line_width(0)
                mask.ctx.rectangle(lower_left[0], lower_left[1], width, height)
                mask.ctx.fill()

                center = self.scale_point(rectangle.position)
                if rectangle.hole_diameter > 0:
                    # Render the center clear
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR
                                          if rectangle.level_polarity == 'dark'
                                             and (not self.invert)
                                          else cairo.OPERATOR_OVER)

                    mask.ctx.arc(center[0], center[1], rectangle.hole_radius * self.scale[0], 0, 2 * math.pi)
                    mask.ctx.fill()

                if rectangle.hole_width > 0 and rectangle.hole_height > 0:
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR
                                          if rectangle.level_polarity == 'dark'
                                             and (not self.invert)
                                          else cairo.OPERATOR_OVER)
                    width, height = self.scale_point((rectangle.hole_width, rectangle.hole_height))
                    lower_left = rotate_point((center[0] - width/2.0, center[1] - height/2.0), rectangle.rotation, center)
                    lower_right = rotate_point((center[0] + width/2.0, center[1] - height/2.0), rectangle.rotation, center)
                    upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0), rectangle.rotation, center)
                    upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0), rectangle.rotation, center)
                    points = (lower_left, lower_right, upper_right, upper_left)
                    mask.ctx.move_to(*points[-1])
                    for point in points:
                        mask.ctx.line_to(*point)
                    mask.ctx.fill()
                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_obround(self, obround, color):
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert)
                                 and obround.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(obround):
            with self._new_mask() as mask:
                mask.ctx.set_line_width(0)

                # Render circles
                for circle in (obround.subshapes['circle1'], obround.subshapes['circle2']):
                    center = self.scale_point(circle.position)
                    mask.ctx.arc(center[0], center[1], (circle.radius * self.scale[0]), 0, (2 * math.pi))
                    mask.ctx.fill()

                # Render Rectangle
                rectangle = obround.subshapes['rectangle']
                lower_left = self.scale_point(rectangle.lower_left)
                width, height = tuple([abs(coord) for coord in
                                       self.scale_point((rectangle.width,
                                                         rectangle.height))])
                mask.ctx.rectangle(lower_left[0], lower_left[1], width, height)
                mask.ctx.fill()

                center = self.scale_point(obround.position)
                if obround.hole_diameter > 0:
                    # Render the center clear
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR)
                    mask.ctx.arc(center[0], center[1], obround.hole_radius * self.scale[0], 0, 2 * math.pi)
                    mask.ctx.fill()

                if obround.hole_width > 0 and obround.hole_height > 0:
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR
                                          if rectangle.level_polarity == 'dark'
                                             and (not self.invert)
                                          else cairo.OPERATOR_OVER)
                    width, height =self.scale_point((obround.hole_width, obround.hole_height))
                    lower_left = rotate_point((center[0] - width / 2.0, center[1] - height / 2.0),
                                              obround.rotation, center)
                    lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0),
                                               obround.rotation, center)
                    upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0),
                                              obround.rotation, center)
                    upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0),
                                               obround.rotation, center)
                    points = (lower_left, lower_right, upper_right, upper_left)
                    mask.ctx.move_to(*points[-1])
                    for point in points:
                        mask.ctx.line_to(*point)
                    mask.ctx.fill()

                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_polygon(self, polygon, color):
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if (not self.invert)
                                 and polygon.level_polarity == 'dark'
                              else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(polygon):
            with self._new_mask() as mask:

                vertices = polygon.vertices
                mask.ctx.set_line_width(0)
                mask.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                # Start from before the end so it is easy to iterate and make sure
                # it is closed
                mask.ctx.move_to(*self.scale_point(vertices[-1]))
                for v in vertices:
                    mask.ctx.line_to(*self.scale_point(v))
                mask.ctx.fill()

                center = self.scale_point(polygon.position)
                if polygon.hole_radius > 0:
                    # Render the center clear
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR
                                          if polygon.level_polarity == 'dark'
                                             and (not self.invert)
                                          else cairo.OPERATOR_OVER)
                    mask.ctx.set_line_width(0)
                    mask.ctx.arc(center[0],
                                 center[1],
                                 polygon.hole_radius * self.scale[0], 0, 2 * math.pi)
                    mask.ctx.fill()

                if polygon.hole_width > 0 and polygon.hole_height > 0:
                    mask.ctx.set_operator(cairo.OPERATOR_CLEAR
                                          if polygon.level_polarity == 'dark'
                                             and (not self.invert)
                                          else cairo.OPERATOR_OVER)
                    width, height = self.scale_point((polygon.hole_width, polygon.hole_height))
                    lower_left = rotate_point((center[0] - width / 2.0, center[1] - height / 2.0),
                                              polygon.rotation, center)
                    lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0),
                                               polygon.rotation, center)
                    upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0),
                                              polygon.rotation, center)
                    upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0),
                                               polygon.rotation, center)
                    points = (lower_left, lower_right, upper_right, upper_left)
                    mask.ctx.move_to(*points[-1])
                    for point in points:
                        mask.ctx.line_to(*point)
                    mask.ctx.fill()

                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_drill(self, circle, color=None):
        color = color if color is not None else self.drill_color
        self._render_circle(circle, color)

    def _render_slot(self, slot, color):
        start = map(mul, slot.start, self.scale)
        end = map(mul, slot.end, self.scale)

        width = slot.diameter

        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if slot.level_polarity == 'dark' and
                                 (not self.invert) else cairo.OPERATOR_CLEAR)
        with self._clip_primitive(slot):
            with self._new_mask() as mask:
                mask.ctx.set_line_width(width * self.scale[0])
                mask.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                mask.ctx.move_to(*start)
                mask.ctx.line_to(*end)
                mask.ctx.stroke()
                self.ctx.mask_surface(mask.surface, self.origin_in_pixels[0])

    def _render_amgroup(self, amgroup, color):
        for primitive in amgroup.primitives:
            self.render(primitive)

    def _render_test_record(self, primitive, color):
        position = [pos + origin for pos, origin in
                    zip(primitive.position, self.origin_in_inch)]
        self.ctx.select_font_face(
            'monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.set_font_size(13)
        self._render_circle(Circle(position, 0.015), color)
        self.ctx.set_operator(cairo.OPERATOR_OVER
                              if primitive.level_polarity == 'dark' and
                              (not self.invert) else cairo.OPERATOR_CLEAR)
        self.ctx.move_to(*[self.scale[0] * (coord + 0.015) for coord in position])
        self.ctx.scale(1, -1)
        self.ctx.show_text(primitive.net_name)
        self.ctx.scale(1, -1)

    def new_render_layer(self, color=None, mirror=False):
        size_in_pixels = self.scale_point(self.size_in_inch)
        matrix = copy.copy(self._xform_matrix)
        layer = cairo.SVGSurface(None, size_in_pixels[0], size_in_pixels[1])
        ctx = cairo.Context(layer)

        if self.invert:
            ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.paint()
        if mirror:
            matrix.xx = -1.0
            matrix.x0 = self.origin_in_pixels[0] + self.size_in_pixels[0]
        self.ctx = ctx
        self.ctx.set_matrix(matrix)
        self.active_layer = layer
        self.active_matrix = matrix

    def flatten(self, color=None, alpha=None):
        color = color if color is not None else self.color
        alpha = alpha if alpha is not None else self.alpha
        self.output_ctx.set_source_rgba(color[0], color[1], color[2], alpha)
        self.output_ctx.mask_surface(self.active_layer)
        self.ctx = None
        self.active_layer = None
        self.active_matrix = None

    def paint_background(self, settings=None):
        color = settings.color if settings is not None else self.background_color
        alpha = settings.alpha if settings is not None else 1.0
        if not self.has_bg:
            self.has_bg = True
            self.output_ctx.set_source_rgba(color[0], color[1], color[2], alpha)
            self.output_ctx.paint()

    def _clip_primitive(self, primitive):
        """ Clip rendering context to pixel-aligned bounding box

        Calculates pixel- and axis- aligned bounding box, and clips current
        context to that region. Improves rendering speed significantly. This
        returns a context manager, use as follows:

            with self._clip_primitive(some_primitive):
                do_rendering_stuff()
                do_more_rendering stuff(with, arguments)

        The context manager will reset the context's clipping region when it
        goes out of scope.

        """
        class Clip:
            def __init__(clp, primitive):
                x_range, y_range = primitive.bounding_box
                xmin, xmax = x_range
                ymin, ymax = y_range

                # Round bounds to the nearest pixel outside of the primitive
                clp.xmin = math.floor(self.scale[0] * xmin)
                clp.xmax = math.ceil(self.scale[0] * xmax)

                # We need to offset Y to take care of the difference in y-pos
                # caused by flipping the axis.
                clp.ymin = math.floor(
                    (self.scale[1] * ymin) - math.ceil(self.origin_in_pixels[1]))
                clp.ymax = math.floor(
                    (self.scale[1] * ymax) - math.floor(self.origin_in_pixels[1]))

                # Calculate width and height, rounded to the nearest pixel
                clp.width = abs(clp.xmax - clp.xmin)
                clp.height = abs(clp.ymax - clp.ymin)

            def __enter__(clp):
                # Clip current context to primitive's bounding box
                self.ctx.rectangle(clp.xmin, clp.ymin, clp.width, clp.height)
                self.ctx.clip()

            def __exit__(clp, exc_type, exc_val, traceback):
                # Reset context clip region
                self.ctx.reset_clip()

        return Clip(primitive)

    def scale_point(self, point):
        return tuple([coord * scale for coord, scale in zip(point, self.scale)])
