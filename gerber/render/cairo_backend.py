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
from operator import mul
import cairocffi as cairo
import math

SCALE = 300.


#class CairoCircle(Circle):
#    def line(self, ctx, x, y, color=(184/255., 115/255., 51/255.)):
#        ctx.set_source_rgb (*color)
#        ctx.set_line_width(self.diameter * SCALE)
#        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
#        ctx.line_to(x * SCALE, y * SCALE)
#        ctx.stroke()
#        
#    def arc(self, ctx, x, y, i, j, direction, color=(184/255., 115/255., 51/255.)):
#        ctx_x, ctx_y = ctx.get_current_point()
#        
#        # Do the math
#        center = ((x + i) * SCALE, (y + j) * SCALE)
#        radius = math.sqrt(math.pow(ctx_x - center[0], 2) + math.pow(ctx_y - center[1], 2))
#        delta_x0 = (ctx_x - center[0])
#        delta_y0 = (ctx_y - center[1])
#        delta_x1 = (x * SCALE - center[0])
#        delta_y1 = (y * SCALE - center[1])
#        theta0 = math.atan2(delta_y0, delta_x0)
#        theta1 = math.atan2(delta_y1, delta_x1)
#        # Draw the arc
#        ctx.set_source_rgb (*color)
#        ctx.set_line_width(self.diameter * SCALE)
#        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
#        if direction == 'clockwise':
#            ctx.arc_negative(center[0], center[1], radius, theta0, theta1)
#        else:
#            ctx.arc(center[0], center[1], radius, theta0, theta1)
#        ctx.stroke()
#
#    def flash(self, ctx, x, y, color=(184/255., 115/255., 51/255.)):
#        ctx.set_source_rgb (*color)
#        ctx.set_line_width(0)
#        ctx.arc(x * SCALE, y * SCALE, (self.diameter/2.) * SCALE, 0, 2 * math.pi)
#        ctx.fill()
#
#class CairoRect(Rect):
#    def line(self, ctx, x, y, color=(184/255., 115/255., 51/255.)):
#        ctx.set_source_rgb (*color)
#        ctx.set_line_width(self.diameter * SCALE)
#        ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
#        ctx.line_to(x * SCALE, y * SCALE)
#        ctx.stroke()
#        
#    def flash(self, ctx, x, y, color=(184/255., 115/255., 51/255.)):
#        xsize, ysize = self.size
#        ctx.set_source_rgb (*color)
#        ctx.set_line_width(0)
#        x0 = SCALE * (x - (xsize / 2.))
#        y0 = SCALE * (y - (ysize / 2.))
#
#        ctx.rectangle(x0,y0,SCALE * xsize, SCALE * ysize)
#        ctx.fill()
#


class GerberCairoContext(GerberContext):
    def __init__(self, surface=None, size=(1000, 1000)):
        GerberContext.__init__(self)
        if surface is None:
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 
                                              size[0], size[1])
        else:
             self.surface = surface
        self.ctx = cairo.Context(self.surface)
        self.size = size
        self.ctx.translate(0, self.size[1])
        self.scale = (SCALE,SCALE)
        self.ctx.scale(1, -1)
        self.apertures = {}
        self.background = False
        
    def set_bounds(self, bounds):
        xbounds, ybounds = bounds
        self.ctx.rectangle(SCALE * xbounds[0], SCALE * ybounds[0], SCALE * (xbounds[1]- xbounds[0]), SCALE * (ybounds[1] - ybounds[0]))
        self.ctx.set_source_rgb(0,0,0)
        self.ctx.fill()

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        self.ctx.set_source_rgb (*color)
        self.ctx.set_line_width(line.width * SCALE)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*start)
        self.ctx.line_to(*end)
        self.ctx.stroke()

    def _render_region(self, region, color):
        points = [tuple(map(mul, point, self.scale)) for point in region.points]
        self.ctx.set_source_rgb (*color)
        self.ctx.set_line_width(0)
        self.ctx.move_to(*points[0])
        for point in points[1:]:
            self.ctx.move_to(*point)
        self.ctx.fill()

    def _render_circle(self, circle, color):
        center = map(mul, circle.position, self.scale)
        self.ctx.set_source_rgb (*color)
        self.ctx.set_line_width(0)
        self.ctx.arc(*center, radius=circle.radius * SCALE, angle1=0, angle2=2 * math.pi)
        self.ctx.fill()

    def _render_rectangle(self, rectangle, color):
        ll = map(mul, rectangle.lower_left, self.scale)
        width, height = tuple(map(mul, (rectangle.width, rectangle.height), map(abs, self.scale)))
        self.ctx.set_source_rgb (*color)
        self.ctx.set_line_width(0)
        self.ctx.rectangle(*ll,width=width, height=height)
        self.ctx.fill()

    def _render_obround(self, obround, color):
        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)

    def _render_drill(self, circle, color):
        self._render_circle(circle, color)

    def dump(self, filename):
        self.surface.write_to_png(filename)