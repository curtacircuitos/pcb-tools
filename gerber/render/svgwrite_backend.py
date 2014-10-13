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


def convert_color(color):
    color = tuple([int(ch * 255) for ch in color])
    return  'rgb(%d, %d, %d)' % color

class SvgCircle(Circle):
    def line(self, ctx, x, y, color='rgb(184, 115, 51)'):
        return ctx.dwg.line(start=(ctx.x * SCALE, -ctx.y * SCALE),
                            end=(x * SCALE, -y * SCALE),
                            stroke=color,
                            stroke_width=SCALE * self.diameter,
                            stroke_linecap="round")

    def arc(self, ctx, x, y, i, j, direction, color='rgb(184, 115, 51)'):
        pass

    def flash(self, ctx, x, y, color='rgb(184, 115, 51)'):
        return [ctx.dwg.circle(center=(x * SCALE, -y * SCALE),
                               r = SCALE * (self.diameter / 2.0),
                               fill=color), ]


class SvgRect(Rect):
    def line(self, ctx, x, y, color='rgb(184, 115, 51)'):
        return ctx.dwg.line(start=(ctx.x * SCALE, -ctx.y * SCALE),
                            end=(x * SCALE, -y * SCALE),
                            stroke=color, stroke_width=2,
                            stroke_linecap="butt")

    def flash(self, ctx, x, y, color='rgb(184, 115, 51)'):
        xsize, ysize = self.size
        return [ctx.dwg.rect(insert=(SCALE * (x - (xsize / 2)),
                                     -SCALE * (y + (ysize / 2))),
                             size=(SCALE * xsize, SCALE * ysize),
                             fill=color), ]


class SvgObround(Obround):
    def line(self, ctx, x, y, color='rgb(184, 115, 51)'):
        pass

    def flash(self, ctx, x, y, color='rgb(184, 115, 51)'):
        xsize, ysize = self.size

        # horizontal obround
        if xsize == ysize:
            return [ctx.dwg.circle(center=(x * SCALE, -y * SCALE),
                                   r = SCALE * (x / 2.0),
                                   fill=color), ]
        if xsize > ysize:
            rectx = xsize - ysize
            recty = ysize
            lcircle = ctx.dwg.circle(center=((x - (rectx / 2.0)) * SCALE,
                                             -y * SCALE),
                                     r = SCALE * (ysize / 2.0),
                                     fill=color)

            rcircle = ctx.dwg.circle(center=((x + (rectx / 2.0)) * SCALE,
                                             -y * SCALE),
                                     r = SCALE * (ysize / 2.0),
                                     fill=color)

            rect = ctx.dwg.rect(insert=(SCALE * (x - (xsize / 2.)),
                                        -SCALE * (y + (ysize / 2.))),
                                size=(SCALE * xsize, SCALE * ysize),
                                fill=color)
            return [lcircle, rcircle, rect, ]

        # Vertical obround
        else:
            rectx = xsize
            recty = ysize - xsize
            lcircle = ctx.dwg.circle(center=(x * SCALE,
                                            (y - (recty / 2.)) * -SCALE),
                                     r = SCALE * (xsize / 2.),
                                     fill=color)

            ucircle = ctx.dwg.circle(center=(x * SCALE,
                                             (y + (recty / 2.)) * -SCALE),
                                     r = SCALE * (xsize / 2.),
                                     fill=color)

            rect = ctx.dwg.rect(insert=(SCALE * (x - (xsize / 2.)),
                                        -SCALE * (y + (ysize / 2.))),
                                size=(SCALE * xsize, SCALE * ysize),
                                fill=color)
            return [lcircle, ucircle, rect, ]


class GerberSvgContext(GerberContext):
    def __init__(self):
        GerberContext.__init__(self)

        self.apertures = {}
        self.dwg = svgwrite.Drawing()
        self.dwg.transform = 'scale 1 -1'
        self.background = False
        self.region_path = None

    def set_bounds(self, bounds):
        xbounds, ybounds = bounds
        size = (SCALE * (xbounds[1] - xbounds[0]), SCALE * (ybounds[1] - ybounds[0]))
        if not self.background:
            self.dwg = svgwrite.Drawing(viewBox='%f, %f, %f, %f' % (SCALE*xbounds[0], -SCALE*ybounds[1],size[0], size[1]))
            self.dwg.add(self.dwg.rect(insert=(SCALE * xbounds[0],
                                               -SCALE * ybounds[1]),
                                       size=size, fill=convert_color(self.background_color)))
            self.background = True

    def set_alpha(self, alpha):
        super(GerberSvgContext, self).set_alpha(alpha)
        import warnings
        warnings.warn('SVG output does not support transparency')

    def define_aperture(self, d, shape, modifiers):
        aperture = None
        if shape == 'C':
            aperture = SvgCircle(diameter=float(modifiers[0][0]))
        elif shape == 'R':
            aperture = SvgRect(size=modifiers[0][0:2])
        elif shape == 'O':
            aperture = SvgObround(size=modifiers[0][0:2])
        self.apertures[d] = aperture

    def stroke(self, x, y, i, j):
        super(GerberSvgContext, self).stroke(x, y, i, j)

        if self.interpolation == 'linear':
            self.line(x, y)
        elif self.interpolation == 'arc':
            self.arc(x, y, i, j)

    def line(self, x, y):
        super(GerberSvgContext, self).line(x, y)
        x, y = self.resolve(x, y)
        ap = self.apertures.get(self.aperture, None)
        if ap is None:
            return
        color = (convert_color(self.color) if self.level_polarity == 'dark' 
                 else convert_color(self.background_color))
        self.dwg.add(ap.line(self, x, y, color))
        self.move(x, y, resolve=False)

    def arc(self, x, y, i, j):
        super(GerberSvgContext, self).arc(x, y, i, j)
        x, y = self.resolve(x, y)
        ap = self.apertures.get(self.aperture, None)
        if ap is None:
            return
        #self.dwg.add(ap.arc(self, x, y, i, j, self.direction,
        #                    convert_color(self.color)))
        self.move(x, y, resolve=False)

    def flash(self, x, y):
        super(GerberSvgContext, self).flash(x, y)
        x, y = self.resolve(x, y)
        ap = self.apertures.get(self.aperture, None)
        if ap is None:
            return
        
        color = (convert_color(self.color) if self.level_polarity == 'dark'
                 else convert_color(self.background_color))
        for shape in ap.flash(self, x, y, color):
            self.dwg.add(shape)
        self.move(x, y, resolve=False)

    def drill(self, x, y, diameter):
        hit = self.dwg.circle(center=(x*SCALE, -y*SCALE),
                              r=SCALE*(diameter/2.0),
                              fill=convert_color(self.drill_color))
        self.dwg.add(hit)

    def region_contour(self, x, y):
        super(GerberSvgContext, self).region_contour(x, y)
        x, y = self.resolve(x, y)
        color = (convert_color(self.color) if self.level_polarity == 'dark'
                 else convert_color(self.background_color))
        if self.region_path is None:
            self.region_path = self.dwg.path(d = 'M %f, %f' %
                                             (self.x*SCALE, -self.y*SCALE),
                                             fill = color, stroke = 'none')
        self.region_path.push('L %f, %f' % (x*SCALE, -y*SCALE))
        self.move(x, y, resolve=False)

    def fill_region(self):
        self.dwg.add(self.region_path)
        self.region_path = None

    def dump(self, filename):
        self.dwg.saveas(filename)
