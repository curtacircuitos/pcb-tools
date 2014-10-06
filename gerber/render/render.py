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

from ..gerber_statements import (
    CommentStmt, UnknownStmt, EofStmt, ParamStmt, CoordStmt, ApertureStmt
)


class GerberContext(object):
    settings = {}

    x = 0
    y = 0

    aperture = 0
    interpolation = 'linear'

    image_polarity = 'positive'
    level_polarity = 'dark'

    def __init__(self):
        pass

    def set_format(self, settings):
        self.settings = settings

    def set_coord_format(self, zero_suppression, format, notation):
        self.settings['zero_suppression'] = zero_suppression
        self.settings['format'] = format
        self.settings['notation'] = notation

    def set_coord_notation(self, notation):
        self.settings['notation'] = notation

    def set_coord_unit(self, unit):
        self.settings['units'] = unit

    def set_image_polarity(self, polarity):
        self.image_polarity = polarity

    def set_level_polarity(self, polarity):
        self.level_polarity = polarity

    def set_interpolation(self, interpolation):
        self.interpolation = 'linear' if interpolation in ("G01", "G1") else 'arc'

    def set_aperture(self, d):
        self.aperture = d

    def resolve(self, x, y):
        return x or self.x, y or self.y

    def define_aperture(self, d, shape, modifiers):
        pass

    def move(self, x, y, resolve=True):
        if resolve:
            self.x, self.y = self.resolve(x, y)
        else:
            self.x, self.y = x, y

    def stroke(self, x, y):
        pass

    def line(self, x, y):
        pass

    def arc(self, x, y):
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

        else:
            raise Exception("Invalid statement to evaluate")

    def _evaluate_param(self, stmt):
        if stmt.param == "FS":
            self.set_coord_format(stmt.zero_suppression, stmt.format, stmt.notation)
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
        if stmt.function in ("G01", "G1", "G02", "G2", "G03", "G3"):
            self.set_interpolation(stmt.function)

        if stmt.op == "D01":
            self.stroke(stmt.x, stmt.y)
        elif stmt.op == "D02":
            self.move(stmt.x, stmt.y)
        elif stmt.op == "D03":
            self.flash(stmt.x, stmt.y)

    def _evaluate_aperture(self, stmt):
        self.set_aperture(stmt.d)
