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

from ..gerber_statements import (CommentStmt, UnknownStmt, EofStmt, ParamStmt,
                                 CoordStmt, ApertureStmt, RegionModeStmt,
                                 QuadrantModeStmt,
)


class GerberContext(object):
    """ Gerber rendering context base class

    Provides basic functionality and API for rendering gerber files.  Medium-
    specific renderers should subclass GerberContext and implement the drawing
    functions. Colors are stored internally as 32-bit RGB and may need to be
    converted to a native format in the rendering subclass.

    Attributes
    ----------
    settings : FileSettings (dict-like)
        Gerber file settings

    x : float
        X-coordinate of the "photoplotter" head.

    y : float
        Y-coordinate of the "photoplotter" head

    aperture : int
        The aperture that is currently in use

    interpolation : str
        Current interpolation mode. may be 'linear' or 'arc'

    direction : string
        Current arc direction. May be either 'clockwise' or 'counterclockwise'

    image_polarity : string
        Current image polarity setting. May be 'positive' or 'negative'

    level_polarity : string
        Level polarity. May be 'dark' or 'clear'. Dark polarity indicates the
        existance of copper/silkscreen/etc. in the exposed area, whereas clear
        polarity indicates material should be removed from the exposed area.

    region_mode : string
        Region mode. May be 'on' or 'off'. When region mode is set to 'on' the
        following "contours" define the outline of a region. When region mode
        is subsequently turned 'off', the defined area is filled.

    quadrant_mode : string
        Quadrant mode. May be 'single-quadrant' or 'multi-quadrant'. Defines
        how arcs are specified.

    color : tuple (<float>, <float>, <float>)
        Color used for rendering as a tuple of normalized (red, green, blue) values.

    drill_color : tuple (<float>, <float>, <float>)
        Color used for rendering drill hits. Format is the same as for `color`.

    background_color : tuple (<float>, <float>, <float>)
        Color of the background. Used when exposing areas in 'clear' level
        polarity mode. Format is the same as for `color`.
    """
    def __init__(self):
        self.settings = {}
        self.x = 0
        self.y = 0

        self.aperture = 0
        self.interpolation = 'linear'
        self.direction = 'clockwise'
        self.image_polarity = 'positive'
        self.level_polarity = 'dark'
        self.region_mode = 'off'
        self.quadrant_mode = 'multi-quadrant'

        self.color = (0.7215, 0.451, 0.200)
        self.drill_color = (0.25, 0.25, 0.25)
        self.background_color = (0.0, 0.0, 0.0)

    def set_format(self, settings):
        """ Set source file format.

        Parameters
        ----------
        settings : FileSettings instance or dict-like
            Gerber file settings used in source file.
        """
        self.settings = settings

    def set_coord_format(self, zero_suppression, decimal_format, notation):
        """ Set coordinate format used in source gerber file

        Parameters
        ----------
        zero_suppression : string
            Zero suppression mode. may be 'leading' or 'trailling'

        decimal_format : tuple (<int>, <int>)
            Decimal precision format specified as (integer digits, decimal digits)

        notation : string
            Notation mode. 'absolute' or 'incremental'
        """
        if zero_suppression not in ('leading', 'trailling'):
            raise ValueError('Zero suppression must be "leading" or "trailing"')
        self.settings['zero_suppression'] = zero_suppression
        self.settings['format'] = decimal_format
        self.settings['notation'] = notation

    def set_coord_notation(self, notation):
        """ Set context notation mode

        Parameters
        ----------
        notation : string
            Notation mode. may be 'absolute' or 'incremental'

        Raises
        ------
        ValueError
            If `notation` is not either "absolute" or "incremental"

        """
        if notation not in ('absolute', 'incremental'):
            raise ValueError('Notation may be "absolute" or "incremental"')
        self.settings['notation'] = notation

    def set_coord_unit(self, unit):
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
        if unit not in ('inch', 'metric'):
            raise ValueError('Unit may be "inch" or "metric"')
        self.settings['units'] = unit

    def set_image_polarity(self, polarity):
        """ Set context image polarity

        Parameters
        ----------
        polarity : string
            Image polarity. May be "positive" or "negative"

        Raises
        ------
        ValueError
            If polarity is not 'positive' or 'negative'
        """
        if polarity not in ('positive', 'negative'):
            raise ValueError('Polarity may be "positive" or "negative"')
        self.image_polarity = polarity

    def set_level_polarity(self, polarity):
        """ Set context level polarity

        Parameters
        ----------
        polarity : string
            Level polarity. May be "dark" or "clear"

        Raises
        ------
        ValueError
            If polarity is not 'dark' or 'clear'
        """
        if polarity not in ('dark', 'clear'):
            raise ValueError('Polarity may be "dark" or "clear"')
        self.level_polarity = polarity

    def set_interpolation(self, interpolation):
        """ Set arc interpolation mode

        Parameters
        ----------
        interpolation : string
            Interpolation mode. May be 'linear' or 'arc'

        Raises
        ------
        ValueError
            If `interpolation` is not 'linear' or 'arc'
        """
        if interpolation not in ('linear', 'arc'):
            raise ValueError('Interpolation may be "linear" or "arc"')
        self.interpolation = interpolation

    def set_aperture(self, d):
        """ Set active aperture

        Parameters
        ----------
        aperture : int
            Aperture number to activate.
        """
        self.aperture = d

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

    def resolve(self, x, y):
        """ Resolve missing x or y coordinates in a coordinate command.

        Replace missing x or y values with the current x or y position. This
        is the default method for handling coordinate pairs pulled from gerber
        file statments, as a move/line/arc involving a change in only one axis
        will drop the redundant axis coordinate to reduce file size.

        Parameters
        ----------
        x : float
            X-coordinate. If `None`, will be replaced with current
            "photoplotter" head x-coordinate

        y : float
            Y-coordinate. If `None`, will be replaced with current
            "photoplotter" head y-coordinate

        Returns
        -------
        coordinates : tuple (<float>, <float>)
            Coordinates in absolute notation
        """
        x = x if x is not None else self.x
        y = y if y is not None else self.y
        return x, y

    def define_aperture(self, d, shape, modifiers):
        pass

    def move(self, x, y, resolve=True):
        """ Lights-off move.

        Move the "photoplotter" head to (x, y) without drawing a line. If x or
        y is `None`, remain at the same point in that axis.

        Parameters
        -----------
        x : float
            X-coordinate to move to. If x is `None`, do not move in the X
            direction

        y : float
            Y-coordinate to move to. if y is `None`, do not move in the Y
            direction

        resolve : bool
            If resolve is `True` the context will replace missing x or y
            coordinates with the current plotter head position. This is the
            default behavior.
        """
        if resolve:
            self.x, self.y = self.resolve(x, y)
        else:
            self.x, self.y = x, y

    def stroke(self, x, y, i, j):
        pass

    def line(self, x, y):
        pass

    def arc(self, x, y, i, j):
        pass

    def flash(self, x, y):
        pass

    def drill(self, x, y, diameter):
        pass

    def evaluate(self, stmt):
        if isinstance(stmt, (CommentStmt, UnknownStmt, EofStmt)):
            return

        elif isinstance(stmt, ParamStmt):
            self._evaluate_param(stmt)

        elif isinstance(stmt, CoordStmt):
            self._evaluate_coord(stmt)

        elif isinstance(stmt, ApertureStmt):
            self._evaluate_aperture(stmt)

        elif isinstance(stmt, (RegionModeStmt, QuadrantModeStmt)):
            self._evaluate_mode(stmt)

        else:
            raise Exception("Invalid statement to evaluate")

    def _evaluate_mode(self, stmt):
        if stmt.type == 'RegionMode':
            if self.region_mode == 'on' and stmt.mode == 'off':
                self._fill_region()
            self.region_mode = stmt.mode
        elif stmt.type == 'QuadrantMode':
            self.quadrant_mode = stmt.mode

    def _evaluate_param(self, stmt):
        if stmt.param == "FS":
            self.set_coord_format(stmt.zero_suppression, stmt.format,
                                  stmt.notation)
            self.set_coord_notation(stmt.notation)
        elif stmt.param == "MO:":
            self.set_coord_unit(stmt.mode)
        elif stmt.param == "IP:":
            self.set_image_polarity(stmt.ip)
        elif stmt.param == "LP:":
            self.set_level_polarity(stmt.lp)
        elif stmt.param == "AD":
            self.define_aperture(stmt.d, stmt.shape, stmt.modifiers)

    def _evaluate_coord(self, stmt):
        if stmt.function in ("G01", "G1"):
            self.set_interpolation('linear')
        elif stmt.function in ('G02', 'G2', 'G03', 'G3'):
            self.set_interpolation('arc')
            self.direction = ('clockwise' if stmt.function in ('G02', 'G2')
                              else 'counterclockwise')
        if stmt.op == "D01":
            self.stroke(stmt.x, stmt.y, stmt.i, stmt.j)
        elif stmt.op == "D02":
            self.move(stmt.x, stmt.y)
        elif stmt.op == "D03":
            self.flash(stmt.x, stmt.y)

    def _evaluate_aperture(self, stmt):
        self.set_aperture(stmt.d)

    def _fill_region(self):
        pass
