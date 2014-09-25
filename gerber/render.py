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

from .parser import CommentStmt, UnknownStmt, EofStmt, ParamStmt, CoordStmt, ApertureStmt

IMAGE_POLARITY_POSITIVE = 1
IMAGE_POLARITY_NEGATIVE = 2

LEVEL_POLARITY_DARK = 1
LEVEL_POLARITY_CLEAR = 2

NOTATION_ABSOLUTE = 1
NOTATION_INCREMENTAL = 2

UNIT_INCH = 1
UNIT_MM = 2

INTERPOLATION_LINEAR = 1
INTERPOLATION_ARC = 2


class GerberCoordFormat(object):
    def __init__(self, zeroes, x, y):
        self.omit_leading_zeroes = True if zeroes == "L" else False
        self.omit_trailing_zeroes = True if zeroes == "T" else False
        self.x_int_digits, self.x_dec_digits = [int(d) for d in x]
        self.y_int_digits, self.y_dec_digits = [int(d) for d in y]

    def resolve(self, x, y):
        new_x = x
        new_y = y

        if new_x is not None:
            negative = "-" in new_x
            new_x = new_x.replace("-", "")

            missing_zeroes = (self.x_int_digits + self.x_dec_digits) - len(new_x)

            if missing_zeroes and self.omit_leading_zeroes:
                new_x = (missing_zeroes * "0") + new_x
            elif missing_zeroes and self.omit_trailing_zeroes:
                new_x += missing_zeroes * "0"

            new_x = float("{0}{1}.{2}".format("-" if negative else "",
                                              new_x[:self.x_int_digits],
                                              new_x[self.x_int_digits:]))

        if new_y is not None:
            negative = "-" in new_y
            new_y = new_y.replace("-", "")

            missing_zeroes = (self.y_int_digits + self.y_dec_digits) - len(new_y)

            if missing_zeroes and self.omit_leading_zeroes:
                new_y = (missing_zeroes * "0") + new_y
            elif missing_zeroes and self.omit_trailing_zeroes:
                new_y += missing_zeroes * "0"

            new_y = float("{0}{1}.{2}".format("-" if negative else "",
                                              new_y[:self.y_int_digits],
                                              new_y[self.y_int_digits:]))

        return new_x, new_y


class GerberContext(object):
    coord_format = None
    coord_notation = NOTATION_ABSOLUTE
    coord_unit = None

    x = 0
    y = 0

    aperture = 0
    interpolation = INTERPOLATION_LINEAR

    image_polarity = IMAGE_POLARITY_POSITIVE
    level_polarity = LEVEL_POLARITY_DARK

    def __init__(self):
        pass

    def set_coord_format(self, zeroes, x, y):
        self.coord_format = GerberCoordFormat(zeroes, x, y)

    def set_coord_notation(self, notation):
        self.coord_notation = NOTATION_ABSOLUTE if notation == "A" else NOTATION_INCREMENTAL

    def set_coord_unit(self, unit):
        self.coord_unit = UNIT_INCH if unit == "IN" else UNIT_MM

    def set_image_polarity(self, polarity):
        self.image_polarity = IMAGE_POLARITY_POSITIVE if polarity == "POS" else IMAGE_POLARITY_NEGATIVE

    def set_level_polarity(self, polarity):
        self.level_polarity = LEVEL_POLARITY_DARK if polarity == "D" else LEVEL_POLARITY_CLEAR

    def set_interpolation(self, interpolation):
        self.interpolation = INTERPOLATION_LINEAR if interpolation in ("G01", "G1") else INTERPOLATION_ARC

    def set_aperture(self, d):
        self.aperture = d

    def resolve(self, x, y):
        x, y = self.coord_format.resolve(x, y)
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
            self.set_coord_format(stmt.zero, stmt.x, stmt.y)
            self.set_coord_notation(stmt.notation)
        elif stmt.param == "MO:":
            self.set_coord_unit(stmt.mo)
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
