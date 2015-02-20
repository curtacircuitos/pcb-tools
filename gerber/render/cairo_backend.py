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

from ..primitives import *

SCALE = 4000.


class GerberCairoContext(GerberContext):
    def __init__(self, surface=None, size=(10000, 10000)):
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
        if not self.background:
            xbounds, ybounds = bounds
            width = SCALE * (xbounds[1] - xbounds[0])
            height = SCALE * (ybounds[1] - ybounds[0])
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width), int(height))
            self.ctx = cairo.Context(self.surface)
            self.ctx.translate(0, height)
            self.scale = (SCALE,SCALE)
            self.ctx.scale(1, -1)
            self.ctx.rectangle(SCALE * xbounds[0], SCALE * ybounds[0], width, height)
            self.ctx.set_source_rgb(0,0,0)
            self.ctx.fill()
            self.background = True

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter if line.aperture.diameter != 0 else 0.001
            self.ctx.set_source_rgba(*color, alpha=self.alpha)
            self.ctx.set_line_width(width * SCALE)
            self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            self.ctx.move_to(*start)
            self.ctx.line_to(*end)
            self.ctx.stroke()
        elif isinstance(line.aperture, Rectangle):
            points = [tuple(map(mul, x, self.scale)) for x in line.vertices]
            self.ctx.set_source_rgba(*color, alpha=self.alpha)
            self.ctx.set_line_width(0)
            self.ctx.move_to(*points[0])
            for point in points[1:]:
                self.ctx.line_to(*point)
            self.ctx.fill()

    def _render_arc(self, arc, color):
        center = map(mul, arc.center, self.scale)
        start = map(mul, arc.start, self.scale)
        end = map(mul, arc.end, self.scale)
        radius = SCALE * arc.radius
        angle1 = arc.start_angle
        angle2 = arc.end_angle
        width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_line_width(width * SCALE)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            self.ctx.arc(*center, radius=radius, angle1=angle1, angle2=angle2)
        else:
            self.ctx.arc_negative(*center, radius=radius, angle1=angle1, angle2=angle2)
        self.ctx.move_to(*end)  # ...lame

    def _render_region(self, region, color):
        points = [tuple(map(mul, point, self.scale)) for point in region.points]
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_line_width(0)
        self.ctx.move_to(*points[0])
        for point in points[1:]:
            self.ctx.line_to(*point)
        self.ctx.fill()

    def _render_circle(self, circle, color):
        center = map(mul, circle.position, self.scale)
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
        self.ctx.set_line_width(0)
        self.ctx.arc(*center, radius=circle.radius * SCALE, angle1=0, angle2=2 * math.pi)
        self.ctx.fill()

    def _render_rectangle(self, rectangle, color):
        ll = map(mul, rectangle.lower_left, self.scale)
        width, height = tuple(map(mul, (rectangle.width, rectangle.height), map(abs, self.scale)))
        self.ctx.set_source_rgba(*color, alpha=self.alpha)
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
