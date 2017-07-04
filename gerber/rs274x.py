#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
# Modified from parser.py by Paulo Henrique Silva <ph.silva@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" This module provides an RS-274-X class and parser.
"""

import copy
import json
import os
import re
import sys

try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO

from .gerber_statements import *
from .primitives import *
from .cam import CamFile, FileSettings
from .utils import sq_distance


def read(filename):
    """ Read data from filename and return a GerberFile

    Parameters
    ----------
    filename : string
        Filename of file to parse

    Returns
    -------
    file : :class:`gerber.rs274x.GerberFile`
        A GerberFile created from the specified file.
    """
    return GerberParser().parse(filename)


def loads(data, filename=None):
    """ Generate a GerberFile object from rs274x data in memory

    Parameters
    ----------
    data : string
        string containing gerber file contents

    filename : string, optional
        string containing the filename of the data source

    Returns
    -------
    file : :class:`gerber.rs274x.GerberFile`
        A GerberFile created from the specified file.
    """
    return GerberParser().parse_raw(data, filename)


class GerberFile(CamFile):
    """ A class representing a single gerber file

    The GerberFile class represents a single gerber file.

    Parameters
    ----------
    statements : list
        list of gerber file statements

    settings : dict
        Dictionary of gerber file settings

    filename : string
        Filename of the source gerber file

    Attributes
    ----------
    comments: list of strings
        List of comments contained in the gerber file.

    size : tuple, (<float>, <float>)
        Size in [self.units] of the layer described by the gerber file.

    bounds: tuple, ((<float>, <float>), (<float>, <float>))
        boundaries of the layer described by the gerber file.
        `bounds` is stored as ((min x, max x), (min y, max y))

    """

    def __init__(self, statements, settings, primitives, apertures, filename=None):
        super(GerberFile, self).__init__(statements, settings, primitives, filename)

        self.apertures = apertures

    @property
    def comments(self):
        return [comment.comment for comment in self.statements
                if isinstance(comment, CommentStmt)]

    @property
    def size(self):
        xbounds, ybounds = self.bounds
        return (xbounds[1] - xbounds[0], ybounds[1] - ybounds[0])

    @property
    def bounds(self):
        min_x = min_y = 1000000
        max_x = max_y = -1000000

        for stmt in [stmt for stmt in self.statements if isinstance(stmt, CoordStmt)]:
            if stmt.x is not None:
                min_x = min(stmt.x, min_x)
                max_x = max(stmt.x, max_x)

            if stmt.y is not None:
                min_y = min(stmt.y, min_y)
                max_y = max(stmt.y, max_y)

        return ((min_x, max_x), (min_y, max_y))

    @property
    def bounding_box(self):
        min_x = min_y = 1000000
        max_x = max_y = -1000000

        for prim in self.primitives:
            bounds = prim.bounding_box
            min_x = min(bounds[0][0], min_x)
            max_x = max(bounds[0][1], max_x)

            min_y = min(bounds[1][0], min_y)
            max_y = max(bounds[1][1], max_y)

        return ((min_x, max_x), (min_y, max_y))

    def write(self, filename, settings=None):
        """ Write data out to a gerber file.
        """
        with open(filename, 'w') as f:
            for statement in self.statements:
                f.write(statement.to_gerber(settings or self.settings))
                f.write("\n")

    def to_inch(self):
        if self.units != 'inch':
            self.units = 'inch'
            for statement in self.statements:
                statement.to_inch()
            for primitive in self.primitives:
                primitive.to_inch()

    def to_metric(self):
        if self.units != 'metric':
            self.units = 'metric'
            for statement in self.statements:
                statement.to_metric()
            for primitive in self.primitives:
                primitive.to_metric()

    def offset(self, x_offset=0,  y_offset=0):
        for statement in self.statements:
            statement.offset(x_offset, y_offset)
        for primitive in self.primitives:
            primitive.offset(x_offset, y_offset)


class GerberParser(object):
    """ GerberParser
    """
    NUMBER = r"[\+-]?\d+"
    DECIMAL = r"[\+-]?\d+([.]?\d+)?"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"
    NAME = r"[a-zA-Z_$\.][a-zA-Z_$\.0-9+\-]+"

    FS = r"(?P<param>FS)(?P<zero>(L|T|D))?(?P<notation>(A|I))[NG0-9]*X(?P<x>[0-7][0-7])Y(?P<y>[0-7][0-7])[DM0-9]*"
    MO = r"(?P<param>MO)(?P<mo>(MM|IN))"
    LP = r"(?P<param>LP)(?P<lp>(D|C))"
    AD_CIRCLE = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>C)[,]?(?P<modifiers>[^,%]*)"
    AD_RECT = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>R)[,](?P<modifiers>[^,%]*)"
    AD_OBROUND = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>O)[,](?P<modifiers>[^,%]*)"
    AD_POLY = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>P)[,](?P<modifiers>[^,%]*)"
    AD_MACRO = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>{name})[,]?(?P<modifiers>[^,%]*)".format(name=NAME)
    AM = r"(?P<param>AM)(?P<name>{name})\*(?P<macro>[^%]*)".format(name=NAME)
    # Include File
    IF = r"(?P<param>IF)(?P<filename>.*)"


    # begin deprecated
    AS = r"(?P<param>AS)(?P<mode>(AXBY)|(AYBX))"
    IN = r"(?P<param>IN)(?P<name>.*)"
    IP = r"(?P<param>IP)(?P<ip>(POS|NEG))"
    IR = r"(?P<param>IR)(?P<angle>{number})".format(number=NUMBER)
    MI = r"(?P<param>MI)(A(?P<a>0|1))?(B(?P<b>0|1))?"
    OF = r"(?P<param>OF)(A(?P<a>{decimal}))?(B(?P<b>{decimal}))?".format(decimal=DECIMAL)
    SF = r"(?P<param>SF)(?P<discarded>.*)"
    LN = r"(?P<param>LN)(?P<name>.*)"
    DEPRECATED_UNIT = re.compile(r'(?P<mode>G7[01])\*')
    DEPRECATED_FORMAT = re.compile(r'(?P<format>G9[01])\*')
    # end deprecated

    PARAMS = (FS, MO, LP, AD_CIRCLE, AD_RECT, AD_OBROUND, AD_POLY,
              AD_MACRO, AM, AS, IF, IN, IP, IR, MI, OF, SF, LN)

    PARAM_STMT = [re.compile(r"%?{0}\*%?".format(p)) for p in PARAMS]

    COORD_FUNCTION = r"G0?[123]"
    COORD_OP = r"D0?[123]"

    COORD_STMT = re.compile((
        r"(?P<function>{function})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, function=COORD_FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(?P<deprecated>(G54)|(G55))?D(?P<d>\d+)\*")

    COMMENT_STMT = re.compile(r"G0?4(?P<comment>[^*]*)(\*)?")

    EOF_STMT = re.compile(r"(?P<eof>M[0]?[012])\*")

    REGION_MODE_STMT = re.compile(r'(?P<mode>G3[67])\*')
    QUAD_MODE_STMT = re.compile(r'(?P<mode>G7[45])\*')

    # Keep include loop from crashing us
    INCLUDE_FILE_RECURSION_LIMIT = 10

    def __init__(self):
        self.filename = None
        self.settings = FileSettings()
        self.statements = []
        self.primitives = []
        self.apertures = {}
        self.macros = {}
        self.current_region = None
        self.x = 0
        self.y = 0
        self.op = "D02"
        self.aperture = 0
        self.interpolation = 'linear'
        self.direction = 'clockwise'
        self.image_polarity = 'positive'
        self.level_polarity = 'dark'
        self.region_mode = 'off'
        self.quadrant_mode = 'multi-quadrant'
        self.step_and_repeat = (1, 1, 0, 0)
        self._recursion_depth = 0

    def parse(self, filename):
        self.filename = filename
        with open(filename, "rU") as fp:
            data = fp.read()
        return self.parse_raw(data, filename)

    def parse_raw(self, data, filename=None):
        self.filename = filename
        for stmt in self._parse(self._split_commands(data)):
            self.evaluate(stmt)
            self.statements.append(stmt)

        # Initialize statement units
        for stmt in self.statements:
            stmt.units = self.settings.units

        return GerberFile(self.statements, self.settings, self.primitives, self.apertures.values(), filename)

    def _split_commands(self, data):
        """
        Split the data into commands. Commands end with * (and also newline to help with some badly formatted files)
        """

        length = len(data)
        start = 0
        in_header = True

        for cur in range(0, length):

            val = data[cur]

            if val == '%' and start == cur:
                in_header = True
                continue

            if val == '\r' or val == '\n':
                if start != cur:
                    yield data[start:cur]
                start = cur + 1

            elif not in_header and val == '*':
                yield data[start:cur + 1]
                start = cur + 1

            elif in_header and val == '%':
                yield data[start:cur + 1]
                start = cur + 1
                in_header = False

    def dump_json(self):
        stmts = {"statements": [stmt.__dict__ for stmt in self.statements]}
        return json.dumps(stmts)

    def dump_str(self):
        string = ""
        for stmt in self.statements:
            string += str(stmt) + "\n"
        return string

    def _parse(self, data):
        oldline = ''

        for line in data:
            line = oldline + line.strip()

            # skip empty lines
            if not len(line):
                continue

            # deal with multi-line parameters
            if line.startswith("%") and not line.endswith("%") and not "%" in line[1:]:
                oldline = line
                continue

            did_something = True  # make sure we do at least one loop
            while did_something and len(line) > 0:
                did_something = False

                # consume empty data blocks
                if line[0] == '*':
                    line = line[1:]
                    did_something = True
                    continue

                # coord
                (coord, r) = _match_one(self.COORD_STMT, line)
                if coord:
                    yield CoordStmt.from_dict(coord, self.settings)
                    line = r
                    did_something = True
                    continue

                # aperture selection
                (aperture, r) = _match_one(self.APERTURE_STMT, line)
                if aperture:
                    yield ApertureStmt(**aperture)
                    did_something = True
                    line = r
                    continue

                # parameter
                (param, r) = _match_one_from_many(self.PARAM_STMT, line)

                if param:
                    if param["param"] == "FS":
                        stmt = FSParamStmt.from_dict(param)
                        self.settings.zero_suppression = stmt.zero_suppression
                        self.settings.format = stmt.format
                        self.settings.notation = stmt.notation
                        yield stmt
                    elif param["param"] == "MO":
                        stmt = MOParamStmt.from_dict(param)
                        self.settings.units = stmt.mode
                        yield stmt
                    elif param["param"] == "LP":
                        yield LPParamStmt.from_dict(param)
                    elif param["param"] == "AD":
                        yield ADParamStmt.from_dict(param)
                    elif param["param"] == "AM":
                        stmt = AMParamStmt.from_dict(param)
                        stmt.units = self.settings.units
                        yield stmt
                    elif param["param"] == "OF":
                        yield OFParamStmt.from_dict(param)
                    elif param["param"] == "IF":
                        # Don't crash on include loop
                        if self._recursion_depth < self.INCLUDE_FILE_RECURSION_LIMIT:
                            self._recursion_depth += 1
                            with open(os.path.join(os.path.dirname(self.filename), param["filename"]), 'r') as f:
                                inc_data = f.read()
                            for stmt in self._parse(self._split_commands(inc_data)):
                                yield stmt
                            self._recursion_depth -= 1
                        else:
                            raise IOError("Include file nesting depth limit exceeded.")
                    elif param["param"] == "IN":
                        yield INParamStmt.from_dict(param)
                    elif param["param"] == "LN":
                        yield LNParamStmt.from_dict(param)
                    # deprecated commands AS, IN, IP, IR, MI, OF, SF, LN
                    elif param["param"] == "AS":
                        yield ASParamStmt.from_dict(param)
                    elif param["param"] == "IN":
                        yield INParamStmt.from_dict(param)
                    elif param["param"] == "IP":
                        yield IPParamStmt.from_dict(param)
                    elif param["param"] == "IR":
                        yield IRParamStmt.from_dict(param)
                    elif param["param"] == "MI":
                        yield MIParamStmt.from_dict(param)
                    elif param["param"] == "OF":
                        yield OFParamStmt.from_dict(param)
                    elif param["param"] == "SF":
                        yield SFParamStmt.from_dict(param)
                    elif param["param"] == "LN":
                        yield LNParamStmt.from_dict(param)
                    else:
                        yield UnknownStmt(line)

                    did_something = True
                    line = r
                    continue

                # Region Mode
                (mode, r) = _match_one(self.REGION_MODE_STMT, line)
                if mode:
                    yield RegionModeStmt.from_gerber(line)
                    line = r
                    did_something = True
                    continue

                # Quadrant Mode
                (mode, r) = _match_one(self.QUAD_MODE_STMT, line)
                if mode:
                    yield QuadrantModeStmt.from_gerber(line)
                    line = r
                    did_something = True
                    continue

                # comment
                (comment, r) = _match_one(self.COMMENT_STMT, line)
                if comment:
                    yield CommentStmt(comment["comment"])
                    did_something = True
                    line = r
                    continue

                # deprecated codes
                (deprecated_unit, r) = _match_one(self.DEPRECATED_UNIT, line)
                if deprecated_unit:
                    stmt = MOParamStmt(param="MO", mo="inch" if "G70" in
                                       deprecated_unit["mode"] else "metric")
                    self.settings.units = stmt.mode
                    yield stmt
                    line = r
                    did_something = True
                    continue

                (deprecated_format, r) = _match_one(self.DEPRECATED_FORMAT, line)
                if deprecated_format:
                    yield DeprecatedStmt.from_gerber(line)
                    line = r
                    did_something = True
                    continue

                # eof
                (eof, r) = _match_one(self.EOF_STMT, line)
                if eof:
                    yield EofStmt()
                    did_something = True
                    line = r
                    continue

                if line.find('*') > 0:
                    yield UnknownStmt(line)
                    did_something = True
                    line = ""
                    continue

            oldline = line

    def evaluate(self, stmt):
        """ Evaluate Gerber statement and update image accordingly.

        This method is called once for each statement in the file as it
        is parsed.

        Parameters
        ----------
        statement : Statement
            Gerber/Excellon statement to evaluate.

        """
        if isinstance(stmt, CoordStmt):
            self._evaluate_coord(stmt)

        elif isinstance(stmt, ParamStmt):
            self._evaluate_param(stmt)

        elif isinstance(stmt, ApertureStmt):
            self._evaluate_aperture(stmt)

        elif isinstance(stmt, (RegionModeStmt, QuadrantModeStmt)):
            self._evaluate_mode(stmt)

        elif isinstance(stmt, (CommentStmt, UnknownStmt, DeprecatedStmt, EofStmt)):
            return

        else:
            raise Exception("Invalid statement to evaluate")

    def _define_aperture(self, d, shape, modifiers):
        aperture = None
        if shape == 'C':
            diameter = modifiers[0][0]

            hole_diameter = 0
            rectangular_hole = (0, 0)
            if len(modifiers[0]) == 2:
                hole_diameter = modifiers[0][1]
            elif len(modifiers[0]) == 3:
                rectangular_hole = modifiers[0][1:3]

            aperture = Circle(position=None, diameter=diameter,
                              hole_diameter=hole_diameter,
                              hole_width=rectangular_hole[0],
                              hole_height=rectangular_hole[1],
                              units=self.settings.units)

        elif shape == 'R':
            width = modifiers[0][0]
            height = modifiers[0][1]

            hole_diameter = 0
            rectangular_hole = (0, 0)
            if len(modifiers[0]) == 3:
                hole_diameter = modifiers[0][2]
            elif len(modifiers[0]) == 4:
                rectangular_hole = modifiers[0][2:4]

            aperture = Rectangle(position=None, width=width, height=height,
                                 hole_diameter=hole_diameter,
                                 hole_width=rectangular_hole[0],
                                 hole_height=rectangular_hole[1],
                                 units=self.settings.units)
        elif shape == 'O':
            width = modifiers[0][0]
            height = modifiers[0][1]

            hole_diameter = 0
            rectangular_hole = (0, 0)
            if len(modifiers[0]) == 3:
                hole_diameter = modifiers[0][2]
            elif len(modifiers[0]) == 4:
                rectangular_hole = modifiers[0][2:4]

            aperture = Obround(position=None, width=width, height=height,
                               hole_diameter=hole_diameter,
                               hole_width=rectangular_hole[0],
                               hole_height=rectangular_hole[1],
                               units=self.settings.units)
        elif shape == 'P':
            outer_diameter = modifiers[0][0]
            number_vertices = int(modifiers[0][1])
            if len(modifiers[0]) > 2:
                rotation = modifiers[0][2]
            else:
                rotation = 0

            hole_diameter = 0
            rectangular_hole = (0, 0)
            if len(modifiers[0]) == 4:
                hole_diameter = modifiers[0][3]
            elif len(modifiers[0]) >= 5:
                rectangular_hole = modifiers[0][3:5]

            aperture = Polygon(position=None, sides=number_vertices,
                               radius=outer_diameter/2.0,
                               hole_diameter=hole_diameter,
                               hole_width=rectangular_hole[0],
                               hole_height=rectangular_hole[1],
                               rotation=rotation)
        else:
            aperture = self.macros[shape].build(modifiers)

        aperture.units = self.settings.units
        self.apertures[d] = aperture

    def _evaluate_mode(self, stmt):
        if stmt.type == 'RegionMode':
            if self.region_mode == 'on' and stmt.mode == 'off':
                # Sometimes we have regions that have no points. Skip those
                if self.current_region:
                    self.primitives.append(Region(self.current_region,
                                                  level_polarity=self.level_polarity, units=self.settings.units))

                self.current_region = None
            self.region_mode = stmt.mode
        elif stmt.type == 'QuadrantMode':
            self.quadrant_mode = stmt.mode

    def _evaluate_param(self, stmt):
        if stmt.param == "FS":
            self.settings.zero_suppression = stmt.zero_suppression
            self.settings.format = stmt.format
            self.settings.notation = stmt.notation
        elif stmt.param == "MO":
            self.settings.units = stmt.mode
        elif stmt.param == "IP":
            self.image_polarity = stmt.ip
        elif stmt.param == "LP":
            self.level_polarity = stmt.lp
        elif stmt.param == "AM":
            self.macros[stmt.name] = stmt
        elif stmt.param == "AD":
            self._define_aperture(stmt.d, stmt.shape, stmt.modifiers)

    def _evaluate_coord(self, stmt):
        x = self.x if stmt.x is None else stmt.x
        y = self.y if stmt.y is None else stmt.y

        if stmt.function in ("G01", "G1"):
            self.interpolation = 'linear'
        elif stmt.function in ('G02', 'G2', 'G03', 'G3'):
            self.interpolation = 'arc'
            self.direction = ('clockwise' if stmt.function in
                              ('G02', 'G2') else 'counterclockwise')

        if stmt.only_function:
            # Sometimes we get a coordinate statement
            # that only sets the function. If so, don't
            # try futher otherwise that might draw/flash something
            return

        if stmt.op:
            self.op = stmt.op
        else:
            # no implicit op allowed, force here if coord block doesn't have it
            stmt.op = self.op

        if self.op == "D01" or self.op == "D1":
            start = (self.x, self.y)
            end = (x, y)

            if self.interpolation == 'linear':
                if self.region_mode == 'off':
                    self.primitives.append(Line(start, end,
                                                self.apertures[self.aperture],
                                                level_polarity=self.level_polarity,
                                                units=self.settings.units))
                else:
                    # from gerber spec revision J3, Section 4.5, page 55:
                    #  The segments are not graphics objects in themselves; segments are part of region which is the graphics object. The segments have no thickness.
                    # The current aperture is associated with the region.
                    # This has no graphical effect, but allows all its attributes to
                    # be applied to the region.

                    if self.current_region is None:
                        self.current_region = [Line(start, end,
                                                    self.apertures.get(self.aperture,
                                                                       Circle((0, 0), 0)),
                                                    level_polarity=self.level_polarity,
                                                    units=self.settings.units), ]
                    else:
                        self.current_region.append(Line(start, end,
                                                        self.apertures.get(self.aperture,
                                                                           Circle((0, 0), 0)),
                                                        level_polarity=self.level_polarity,
                                                        units=self.settings.units))
            else:
                i = 0 if stmt.i is None else stmt.i
                j = 0 if stmt.j is None else stmt.j
                center = self._find_center(start, end, (i, j))
                if self.region_mode == 'off':
                    self.primitives.append(Arc(start, end, center, self.direction,
                                               self.apertures[self.aperture],
                                               quadrant_mode=self.quadrant_mode,
                                               level_polarity=self.level_polarity,
                                               units=self.settings.units))
                else:
                    if self.current_region is None:
                        self.current_region = [Arc(start, end, center, self.direction,
                                                   self.apertures.get(self.aperture, Circle((0,0), 0)),
                                                   quadrant_mode=self.quadrant_mode,
                                                   level_polarity=self.level_polarity,
                                                   units=self.settings.units),]
                    else:
                        self.current_region.append(Arc(start, end, center, self.direction,
                                                       self.apertures.get(self.aperture, Circle((0,0), 0)),
                                                       quadrant_mode=self.quadrant_mode,
                                                       level_polarity=self.level_polarity,
                                                       units=self.settings.units))
                    # Gerbv seems to reset interpolation mode in regions..
                    # TODO: Make sure this is right.
                    self.interpolation = 'linear'

        elif self.op == "D02" or self.op == "D2":

            if self.region_mode == "on":
                # D02 in the middle of a region finishes that region and starts a new one
                if self.current_region and len(self.current_region) > 1:
                    self.primitives.append(Region(self.current_region,
                                                  level_polarity=self.level_polarity,
                                                  units=self.settings.units))
                self.current_region = None

        elif self.op == "D03" or self.op == "D3":
            primitive = copy.deepcopy(self.apertures[self.aperture])

            if primitive is not None:

                if not isinstance(primitive, AMParamStmt):
                    primitive.position = (x, y)
                    primitive.level_polarity = self.level_polarity
                    primitive.units = self.settings.units
                    self.primitives.append(primitive)
                else:
                    # Aperture Macro
                    for am_prim in primitive.primitives:
                        renderable = am_prim.to_primitive((x, y),
                                                          self.level_polarity,
                                                          self.settings.units)
                        if renderable is not None:
                            self.primitives.append(renderable)
        self.x, self.y = x, y

    def _find_center(self, start, end, offsets):
        """
        In single quadrant mode, the offsets are always positive, which means
        there are 4 possible centers. The correct center is the only one that
        results in an arc with sweep angle of less than or equal to 90 degrees
        in the specified direction
        """
        two_pi = 2 * math.pi
        if self.quadrant_mode == 'single-quadrant':
            # The Gerber spec says single quadrant only has one possible center,
            # and you can detect it based on the angle. But for real files, this
            # seems to work better - there is usually only one option that makes
            # sense for the center (since the distance should be the same
            # from start and end). We select the center with the least error in
            # radius from all the options with a valid sweep angle.

            sqdist_diff_min = sys.maxsize
            center = None
            for factors in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:

                test_center = (start[0] + offsets[0] * factors[0],
                               start[1] + offsets[1] * factors[1])

                # Find angle from center to start and end points
                start_angle = math.atan2(*reversed([_start - _center for _start, _center in zip(start, test_center)]))
                end_angle = math.atan2(*reversed([_end - _center for _end, _center in zip(end, test_center)]))

                # Clamp angles to 0, 2pi
                theta0 = (start_angle + two_pi) % two_pi
                theta1 = (end_angle + two_pi) % two_pi

                # Determine sweep angle in the current arc direction
                if self.direction == 'counterclockwise':
                    sweep_angle = abs(theta1 - theta0)
                else:
                    theta0 += two_pi
                    sweep_angle = abs(theta0 - theta1) % two_pi

                # Calculate the radius error
                sqdist_start = sq_distance(start, test_center)
                sqdist_end = sq_distance(end, test_center)
                sqdist_diff = abs(sqdist_start - sqdist_end)

                # Take the option with the lowest radius error from the set of
                # options with a valid sweep angle
                # In some rare cases, the sweep angle is numerically (10**-14) above pi/2
                # So it is safer to compare the angles with some tolerance
                is_lowest_radius_error = sqdist_diff < sqdist_diff_min
                is_valid_sweep_angle = sweep_angle >= 0 and sweep_angle <= math.pi / 2.0 + 1e-6
                if is_lowest_radius_error and is_valid_sweep_angle:
                    center = test_center
                    sqdist_diff_min = sqdist_diff
            return center
        else:
            return (start[0] + offsets[0], start[1] + offsets[1])

    def _evaluate_aperture(self, stmt):
        self.aperture = stmt.d

def _match_one(expr, data):
    match = expr.match(data)
    if match is None:
        return ({}, None)
    else:
        return (match.groupdict(), data[match.end(0):])


def _match_one_from_many(exprs, data):
    for expr in exprs:
        match = expr.match(data)
        if match:
            return (match.groupdict(), data[match.end(0):])

    return ({}, None)
