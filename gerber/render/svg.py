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
from .apertures import Circle, Rect, Obround, Polygon
import svgwrite

SCALE = 300


class SvgCircle(Circle):
    def draw(self, ctx, x, y):
        return ctx.dwg.line(start=(ctx.x * SCALE, -ctx.y * SCALE),
                            end=(x * SCALE, -y * SCALE),
                            stroke="rgb(184, 115, 51)",
                            stroke_width=SCALE * self.diameter,
                            stroke_linecap="round")

    def flash(self, ctx, x, y):
        return [ctx.dwg.circle(center=(x * SCALE, -y * SCALE),
                              r = SCALE * (self.diameter / 2.0),
                              fill='rgb(184, 115, 51)'),]


class SvgRect(Rect):
    def draw(self, ctx, x, y):
        return ctx.dwg.line(start=(ctx.x * SCALE, -ctx.y * SCALE),
                            end=(x * SCALE, -y * SCALE),
                            stroke="rgb(184, 115, 51)", stroke_width=2,
                            stroke_linecap="butt")

    def flash(self, ctx, x, y):
        xsize, ysize = self.size
        return [ctx.dwg.rect(insert=(SCALE * (x - (xsize / 2)),
                                    -SCALE * (y + (ysize / 2))),
                            size=(SCALE * xsize, SCALE * ysize),
                            fill="rgb(184, 115, 51)"),]

class SvgObround(Obround):
    def draw(self, ctx, x, y):
        pass
    
    def flash(self, ctx, x, y):
        xsize, ysize = self.size
        
        # horizontal obround
        if xsize == ysize:
            return [ctx.dwg.circle(center=(x * SCALE, -y * SCALE),
                              r = SCALE * (x / 2.0),
                              fill='rgb(184, 115, 51)'),]
        if xsize > ysize:
            rectx = xsize - ysize
            recty = ysize
            lcircle = ctx.dwg.circle(center=((x - (rectx / 2.0)) * SCALE,
                                            -y * SCALE),
                                     r = SCALE * (ysize / 2.0),
                                     fill='rgb(184, 115, 51)')
            
            rcircle = ctx.dwg.circle(center=((x + (rectx / 2.0)) * SCALE,
                                            -y * SCALE),
                                     r = SCALE * (ysize / 2.0),
                                     fill='rgb(184, 115, 51)')
        
            rect = ctx.dwg.rect(insert=(SCALE * (x - (xsize / 2.)),
                                        -SCALE * (y + (ysize / 2.))),
                                size=(SCALE * xsize, SCALE * ysize),
                                fill='rgb(184, 115, 51)')
            return [lcircle, rcircle, rect,]
        
        # Vertical obround
        else:
            rectx = xsize
            recty = ysize - xsize
            lcircle = ctx.dwg.circle(center=(x * SCALE,
                                            (y - (recty / 2.)) * -SCALE),
                                     r = SCALE * (xsize / 2.),
                                     fill='rgb(184, 115, 51)')
            
            ucircle = ctx.dwg.circle(center=(x * SCALE,
                                             (y + (recty / 2.)) * -SCALE),
                                     r = SCALE * (xsize / 2.),
                                     fill='rgb(184, 115, 51)')
        
            rect = ctx.dwg.rect(insert=(SCALE * (x - (xsize / 2.)),
                                        -SCALE * (y + (ysize / 2.))),
                                size=(SCALE * xsize, SCALE * ysize),
                                fill='rgb(184, 115, 51)')
            return [lcircle, ucircle, rect,]
    

class GerberSvgContext(GerberContext):
    def __init__(self):
        GerberContext.__init__(self)

        self.apertures = {}
        self.dwg = svgwrite.Drawing()
        #self.dwg.add(self.dwg.rect(insert=(0, 0), size=(2000, 2000), fill="black"))

    def set_bounds(self, bounds):
        xbounds, ybounds =  bounds
        size = (SCALE * (xbounds[1] - xbounds[0]), SCALE * (ybounds[1] - ybounds[0]))
        self.dwg.add(self.dwg.rect(insert=(SCALE * xbounds[0], -SCALE * ybounds[1]), size=size, fill="black"))
        

    def define_aperture(self, d, shape, modifiers):
        aperture = None
        if shape == 'C':
            aperture = SvgCircle(diameter=float(modifiers[0][0]))
        elif shape == 'R':
            aperture = SvgRect(size=modifiers[0][0:2])
        elif shape == 'O':
            aperture = SvgObround(size=modifiers[0][0:2])
        self.apertures[d] = aperture

    def stroke(self, x, y):
        super(GerberSvgContext, self).stroke(x, y)

        if self.interpolation == 'linear':
            self.line(x, y)
        elif self.interpolation == 'arc':
            #self.arc(x, y)
            self.line(x,y)

    def line(self, x, y):
        super(GerberSvgContext, self).line(x, y)
        x, y = self.resolve(x, y)
        ap = self.apertures.get(self.aperture, None)
        if ap is None:
            return
        self.dwg.add(ap.draw(self, x, y))
        self.move(x, y, resolve=False)


    def arc(self, x, y):
        super(GerberSvgContext, self).arc(x, y)


    def flash(self, x, y):
        super(GerberSvgContext, self).flash(x, y)
        x, y = self.resolve(x, y)
        ap = self.apertures.get(self.aperture, None)
        if ap is None:
            return
        for shape in ap.flash(self, x, y):
            self.dwg.add(shape)
        self.move(x, y, resolve=False)


    def drill(self, x, y, diameter):
        hit = self.dwg.circle(center=(x*SCALE, -y*SCALE), r=SCALE*(diameter/2.0), fill='gray')
        self.dwg.add(hit)

    def dump(self, filename):
        self.dwg.saveas(filename)
        
        
