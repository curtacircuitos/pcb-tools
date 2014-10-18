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
from ..gerber_statements import (CommentStmt, UnknownStmt, EofStmt, ParamStmt,
                                 CoordStmt, ApertureStmt, RegionModeStmt,
                                 QuadrantModeStmt,
)

from ..primitives import *

class GerberContext(object):
    """ Gerber rendering context base class

    Provides basic functionality and API for rendering gerber files.  Medium-
    specific renderers should subclass GerberContext and implement the drawing
    functions. Colors are stored internally as 32-bit RGB and may need to be
    converted to a native format in the rendering subclass.

    Attributes
    ----------
    units : string
        Measurement units

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
        self.units = units
        self.color = (0.7215, 0.451, 0.200)
        self.drill_color = (0.25, 0.25, 0.25)
        self.background_color = (0.0, 0.0, 0.0)
        self.alpha = 1.0

    def set_units(self, units):
        """ Set context measurement units

        Parameters
        ----------
        unit : string
            Measurement units. may be 'inch' or 'metric'

        Raises
        ------
        ValueError
            If `unit` is not 'inch' or 'metric'
        """
        if units not in ('inch', 'metric'):
            raise ValueError('Units may be "inch" or "metric"')
        self.units = units

    def set_color(self, color):
        """ Set rendering color.

        Parameters
        ----------
        color : tuple (<float>, <float>, <float>)
            Color as a tuple of (red, green, blue) values. Each channel is
            represented as a float value in (0, 1)
        """
        self.color = color

    def set_drill_color(self, color):
        """ Set color used for rendering drill hits.

        Parameters
        ----------
        color : tuple (<float>, <float>, <float>)
            Color as a tuple of (red, green, blue) values. Each channel is
            represented as a float value in (0, 1)
        """
        self.drill_color = color

    def set_background_color(self, color):
        """ Set rendering background color

        Parameters
        ----------
        color : tuple (<float>, <float>, <float>)
            Color as a tuple of (red, green, blue) values. Each channel is
            represented as a float value in (0, 1)
        """
        self.background_color = color

    def set_alpha(self, alpha):
        """ Set layer rendering opacity

        .. note::
            Not all backends/rendering devices support this parameter.

        Parameters
        ----------
        alpha : float
            Rendering opacity. must be between 0.0 (transparent) and 1.0 (opaque)
        """
        self.alpha = alpha

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
            self._render_polygon(Polygon, color)
        elif isinstance(primitive, Drill):
            self._render_drill(primitive, self.drill_color)
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

