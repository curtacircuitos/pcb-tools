#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .render import GerberContext, INTERPOLATION_LINEAR, INTERPOLATION_ARC
import svgwrite


class Shape(object):
    pass


class Circle(Shape):
    def __init__(self, diameter=0.0):
        self.diameter = diameter

    def draw(self, ctx, x, y):
        return ctx.dwg.line(start=(ctx.x*300, ctx.y*300), end=(x*300, y*300), stroke="rgb(184, 115, 51)",
                            stroke_width=2, stroke_linecap="round")

    def flash(self, ctx, x, y):
        return ctx.dwg.circle(center=(x*300, y*300), r=300*(self.diameter/2.0), fill="rgb(184, 115, 51)")


class Rect(Shape):
    def __init__(self, size=(0, 0)):
        self.size = size

    def draw(self, ctx, x, y):
        return ctx.dwg.line(start=(ctx.x*300, ctx.y*300), end=(x*300, y*300), stroke="rgb(184, 115, 51)",
                            stroke_width=2, stroke_linecap="butt")

    def flash(self, ctx, x, y):
        # Center the rectange on x,y
        x -= (self.size[0] / 2.0)
        y -= (self.size[0] / 2.0)
        return ctx.dwg.rect(insert=(300*x, 300*y), size=(300*float(self.size[0]), 300*float(self.size[1])),
                            fill="rgb(184, 115, 51)")


class GerberSvgContext(GerberContext):
    def __init__(self):
        GerberContext.__init__(self)

        self.apertures = {}
        self.dwg = svgwrite.Drawing()
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(2000, 2000), fill="black"))

    def define_aperture(self, d, shape, modifiers):
        aperture = None
        if shape == "C":
            aperture = Circle(diameter=float(modifiers[0][0]))
        elif shape == "R":
            aperture = Rect(size=modifiers[0][0:2])

        self.apertures[d] = aperture

    def stroke(self, x, y):
        super(GerberSvgContext, self).stroke(x, y)

        if self.interpolation == INTERPOLATION_LINEAR:
            self.line(x, y)
        elif self.interpolation == INTERPOLATION_ARC:
            self.arc(x, y)

    def line(self, x, y):
        super(GerberSvgContext, self).line(x, y)

        x, y = self.resolve(x, y)

        ap = self.apertures.get(str(self.aperture), None)
        if ap is None:
            return

        self.dwg.add(ap.draw(self, x, y))

        self.move(x, y, resolve=False)

    def arc(self, x, y):
        super(GerberSvgContext, self).arc(x, y)

    def flash(self, x, y):
        super(GerberSvgContext, self).flash(x, y)

        x, y = self.resolve(x, y)

        ap = self.apertures.get(str(self.aperture), None)
        if ap is None:
            return

        self.dwg.add(ap.flash(self, x, y))

        self.move(x, y, resolve=False)

    def drill(self, x, y, diameter):
        hit = self.dwg.circle(center=(x*300, y*300), r=300*(diameter/2.0), fill="gray")
        self.dwg.add(hit)
        
        
    def dump(self,filename='teste.svg'):
        self.dwg.saveas(filename)
