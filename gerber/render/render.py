#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
# Modified from code by Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Rendering
============
**Gerber (RS-274X) and Excellon file rendering**

Render Gerber and Excellon files to a variety of formats. The render module
currently supports SVG rendering using the `svgwrite` library.
"""


from ..primitives import *
from ..gerber_statements import (CommentStmt, UnknownStmt, EofStmt, ParamStmt,
                                 CoordStmt, ApertureStmt, RegionModeStmt,
                                 QuadrantModeStmt,)


class GerberContext(object):
    """ Gerber rendering context base class

    Provides basic functionality and API for rendering gerber files.  Medium-
    specific renderers should subclass GerberContext and implement the drawing
    functions. Colors are stored internally as 32-bit RGB and may need to be
    converted to a native format in the rendering subclass.

    Attributes
    ----------
    units : string
        Measurement units. 'inch' or 'metric'

    color : tuple (<float>, <float>, <float>)
        Color used for rendering as a tuple of normalized (red, green, blue) values.

    drill_color : tuple (<float>, <float>, <float>)
        Color used for rendering drill hits. Format is the same as for `color`.

    background_color : tuple (<float>, <float>, <float>)
        Color of the background. Used when exposing areas in 'clear' level
        polarity mode. Format is the same as for `color`.

    alpha : float
        Rendering opacity. Between 0.0 (transparent) and 1.0 (opaque.)
    """
    def __init__(self, units='inch'):
        self._units = units
        self._color = (0.7215, 0.451, 0.200)
        self._drill_color = (0.25, 0.25, 0.25)
        self._background_color = (0.0, 0.0, 0.0)
        self._alpha = 1.0
        self._invert = False

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, units):
        if units not in ('inch', 'metric'):
            raise ValueError('Units may be "inch" or "metric"')
        self._units = units

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if len(color) != 3:
            raise TypeError('Color must be a tuple of R, G, and B values')
        for c in color:
            if c < 0 or c > 1:
                raise ValueError('Channel values must be between 0.0 and 1.0')
        self._color = color

    @property
    def drill_color(self):
        return self._drill_color

    @drill_color.setter
    def drill_color(self, color):
        if len(color) != 3:
            raise TypeError('Drill color must be a tuple of R, G, and B values')
        for c in color:
            if c < 0 or c > 1:
                raise ValueError('Channel values must be between 0.0 and 1.0')
        self._drill_color = color

    @property
    def background_color(self):
        return self._background_color

    @background_color.setter
    def background_color(self, color):
        if len(color) != 3:
            raise TypeError('Background color must be a tuple of R, G, and B values')
        for c in color:
            if c < 0 or c > 1:
                raise ValueError('Channel values must be between 0.0 and 1.0')
        self._background_color = color

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha):
        if alpha < 0 or alpha > 1:
            raise ValueError('Alpha must be between 0.0 and 1.0')
        self._alpha = alpha

    @property
    def invert(self):
        return self._invert

    @invert.setter
    def invert(self, invert):
        self._invert = invert

    def render(self, primitive):
        color = (self.color if primitive.level_polarity == 'dark'
                 else self.background_color)
        if isinstance(primitive, Line):
            self._render_line(primitive, color)
        elif isinstance(primitive, Arc):
            self._render_arc(primitive, color)
        elif isinstance(primitive, Region):
            self._render_region(primitive, color)
        elif isinstance(primitive, Circle):
            self._render_circle(primitive, color)
        elif isinstance(primitive, Rectangle):
            self._render_rectangle(primitive, color)
        elif isinstance(primitive, Obround):
            self._render_obround(primitive, color)
        elif isinstance(primitive, Polygon):
            self._render_polygon(primitive, color)
        elif isinstance(primitive, Drill):
            self._render_drill(primitive, self.drill_color)
        elif isinstance(primitive, TestRecord):
            self._render_test_record(primitive, color)
        else:
            return

    def _render_line(self, primitive, color):
        pass

    def _render_arc(self, primitive, color):
        pass

    def _render_region(self, primitive, color):
        pass

    def _render_circle(self, primitive, color):
        pass

    def _render_rectangle(self, primitive, color):
        pass

    def _render_obround(self, primitive, color):
        pass

    def _render_polygon(self, primitive, color):
        pass

    def _render_drill(self, primitive, color):
        pass

    def _render_test_record(self, primitive, color):
        pass


class Renderable(object):
    def __init__(self, color=None, alpha=None, invert=False):
        self.color = color
        self.alpha = alpha
        self.invert = invert

    def to_render(self):
        """ Override this in subclass. Should return a list of Primitives or Renderables
        """
        raise NotImplementedError('to_render() must be implemented in subclass')

    def apply_theme(self, theme):
        raise NotImplementedError('apply_theme() must be implemented in subclass')
