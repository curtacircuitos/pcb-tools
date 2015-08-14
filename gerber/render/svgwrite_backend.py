#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
# Based on render_svg.py by Paulo Henrique Silva <ph.silva@gmail.com>

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
import math
import svgwrite

from ..primitives import *

SCALE = 400.


def svg_color(color):
    color = tuple([int(ch * 255) for ch in color])
    return  'rgb(%d, %d, %d)' % color


class GerberSvgContext(GerberContext):
    def __init__(self):
        GerberContext.__init__(self)
        self.scale = (SCALE, -SCALE)
        self.dwg = svgwrite.Drawing()
        self.draw_object = self.dwg
        self.background = False

    def group(self, id):
        """ Set or remove a group.
        params:
            id - id to assign to the group

        if id is None the group is no longer used and any drawing will happen
        in the root Drawing object
        """
        if id is None:
            self.draw_object = self.dwg
        else:
            self.draw_object = self.dwg.add(self.dwg.g(id=id))
    
    def dump_text(self):
        """ Return the underlying SVG as text """
        return self.dwg.tostring()

    def dump(self, filename):
        self.dwg.saveas(filename)

    def set_bounds(self, bounds):
        xbounds, ybounds = bounds
        size = (SCALE * (xbounds[1] - xbounds[0]),
                SCALE * (ybounds[1] - ybounds[0]))
        if not self.background:
            vbox = '%f, %f, %f, %f' % (SCALE * xbounds[0], -SCALE * ybounds[1],
                                       size[0], size[1])
            self.dwg = svgwrite.Drawing(viewBox=vbox)
            self.draw_object = self.dwg
            rect = self.dwg.rect(insert=(SCALE * xbounds[0],
                                         -SCALE * ybounds[1]),
                                 size=size,
                                 fill=svg_color(self.background_color))
            self.draw_object.add(rect)
            self.background = True

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter if line.aperture.diameter != 0 else 0.001
            aline = self.dwg.line(start=start, end=end,
                                  stroke=svg_color(color),
                                  stroke_width=SCALE * width,
                                  stroke_linecap='round')
            aline.stroke(opacity=self.alpha)
            self.draw_object.add(aline)
        elif isinstance(line.aperture, Rectangle):
            points = [tuple(map(mul, point, self.scale)) for point in line.vertices]
            path = self.dwg.path(d='M %f, %f' % points[0],
                                 fill=svg_color(color),
                                 stroke='none')
            path.fill(opacity=self.alpha)
            for point in points[1:]:
                path.push('L %f, %f' % point)
            self.draw_object.add(path)

    def _render_arc(self, arc, color):
        start = tuple(map(mul, arc.start, self.scale))
        end = tuple(map(mul, arc.end, self.scale))
        radius = SCALE * arc.radius
        width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.001
        arc_path = self.dwg.path(d='M %f, %f' % start,
                                    stroke=svg_color(color),
                                    stroke_width=SCALE * width)
        large_arc = arc.sweep_angle >= 2 * math.pi
        direction = '-' if arc.direction == 'clockwise' else '+'
        arc_path.push_arc(end, 0, radius, large_arc, direction, True)
        self.draw_object.add(arc_path)

    def _render_region(self, region, color):
        points = [tuple(map(mul, point, self.scale)) for point in region.points]
        region_path = self.dwg.path(d='M %f, %f' % points[0],
                                    fill=svg_color(color),
                                    stroke='none')
        region_path.fill(opacity=self.alpha)
        for point in points[1:]:
            region_path.push('L %f, %f' % point)
        self.draw_object.add(region_path)

    def _render_circle(self, circle, color):
        center = map(mul, circle.position, self.scale)
        acircle = self.dwg.circle(center=center,
                                  r = SCALE * circle.radius,
                                  fill=svg_color(color))
        acircle.fill(opacity=self.alpha)
        self.draw_object.add(acircle)

    def _render_rectangle(self, rectangle, color):
        center = tuple(map(mul, rectangle.position, self.scale))
        size = tuple(map(mul, (rectangle.width, rectangle.height), map(abs, self.scale)))
        insert = center[0] - size[0] / 2., center[1] - size[1] / 2.
        arect = self.dwg.rect(insert=insert, size=size,
                              fill=svg_color(color))
        arect.fill(opacity=self.alpha)
        self.draw_object.add(arect)

    def _render_obround(self, obround, color):
        self._render_circle(obround.subshapes['circle1'], color)
        self._render_circle(obround.subshapes['circle2'], color)
        self._render_rectangle(obround.subshapes['rectangle'], color)


    def _render_drill(self, circle, color):
        center = map(mul, circle.position, self.scale)
        hit = self.dwg.circle(center=center, r=SCALE * circle.radius,
                              fill=svg_color(color))
        self.draw_object.add(hit)
