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
import re

from .gerber_statements import *
from .primitives import *
from .cam import CamFile, FileSettings


def read(filename, add_debug_comment_statement=False):
    """ Read data from filename and return a GerberFile

    Parameters
    ----------
    filename : string
        Filename of file to parse

    add_debug_comment_statement: True. False; default to False
        Will add 'G04' statements into the read GerberFile class to indicate 
        where each primitives have been discovered.

    Returns
    -------
    file : :class:`gerber.rs274x.GerberFile`
        A GerberFile created from the specified file.
    """
    return GerberParser(add_debug_comment_statement=add_debug_comment_statement).parse(filename)


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
    def __init__(self, statements, settings, primitives, filename=None):
        super(GerberFile, self).__init__(statements, settings, primitives, filename)


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

    def write(self, filename, settings=None):
        """ Write data out to a gerber file
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


#    def apply(self, *ops):
#        #for statement in self.statements:
#        #    statement.apply()
#        for primitive in self.primitives:
#            primitive.apply()


class GerberParser(object):
    """ GerberParser
    """
    NUMBER = r"[\+-]?\d+"
    DECIMAL = r"[\+-]?\d+([.]?\d+)?"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"
    NAME = r"[a-zA-Z_$][a-zA-Z_$0-9]+"
    FUNCTION = r"G\d{2}"

    COORD_OP = r"D[0]?[123]"

    FS = r"(?P<param>FS)(?P<zero>(L|T))?(?P<notation>(A|I))X(?P<x>[0-7][0-7])Y(?P<y>[0-7][0-7])"
    MO = r"(?P<param>MO)(?P<mo>(MM|IN))"
    LP = r"(?P<param>LP)(?P<lp>(D|C))"
    AD_CIRCLE = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>C)[,]?(?P<modifiers>[^,]*)?"
    AD_RECT = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>R)[,](?P<modifiers>[^,]*)"
    AD_OBROUND = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>O)[,](?P<modifiers>[^,]*)"
    AD_POLY = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>P)[,](?P<modifiers>[^,]*)"
    AD_MACRO = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>{name})[,]?(?P<modifiers>[^,]*)?".format(name=NAME)
    AM = r"(?P<param>AM)(?P<name>{name})\*(?P<macro>.*)".format(name=NAME)

    # begin deprecated
    AS = r"(?P<param>AS)(?P<mode>(AXBY)|(AYBX))"
    IN = r"(?P<param>IN)(?P<name>.*)"
    IP = r"(?P<param>IP)(?P<ip>(POS|NEG))"
    IR = r"(?P<param>IR)(?P<angle>{number})".format(number=NUMBER)
    MI = r"(?P<param>MI)(A(?P<a>0|1))?(B(?P<b>0|1))?"
    OF = r"(?P<param>OF)(A(?P<a>{decimal}))?(B(?P<b>{decimal}))?".format(decimal=DECIMAL)
    SF = r"(?P<param>SF)(?P<discarded>.*)"
    LN = r"(?P<param>LN)(?P<name>.*)"
    # end deprecated

    PARAMS = (FS, MO, LP, AD_CIRCLE, AD_RECT, AD_OBROUND, AD_POLY, AD_MACRO, AM, AS, IN, IP, IR, MI, OF, SF, LN)
    PARAM_STMT = [re.compile(r"%?{0}\*%?".format(p)) for p in PARAMS]

    COORD_STMT = re.compile((
        r"(?P<function>{function})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, function=FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(?P<deprecated>(G54)|G55)?D(?P<d>\d+)\*")


    COMMENT_STMT = re.compile(r"G04(?P<comment>[^*]*)(\*)?")

    EOF_STMT = re.compile(r"(?P<eof>M02)\*")

    REGION_MODE_STMT = re.compile(r'(?P<mode>G3[67])\*')
    QUAD_MODE_STMT = re.compile(r'(?P<mode>G7[45])\*')

    def __init__(self, add_debug_comment_statement=False):
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
        self.add_debug_comment_statement = add_debug_comment_statement


    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        for stmt in self._parse(data):
            self.evaluate(stmt)
            self.statements.append(stmt)

        return GerberFile(self.statements, self.settings, self.primitives, filename)

    def dump_json(self):
        stmts = {"statements": [stmt.__dict__ for stmt in self.statements]}
        return json.dumps(stmts)

    def dump_str(self):
        s = ""
        for stmt in self.statements:
            s += str(stmt) + "\n"
        return s

    def _parse(self, data):
        oldline = ''

        for i, line in enumerate(data):
            line = oldline + line.strip()

            # skip empty lines
            if not len(line):
                continue

            # deal with multi-line parameters
            if line.startswith("%") and not line.endswith("%"):
                oldline = line
                continue

            did_something = True  # make sure we do at least one loop
            while did_something and len(line) > 0:
                did_something = False

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

                # comment
                (comment, r) = _match_one(self.COMMENT_STMT, line)
                if comment:
                    yield CommentStmt(comment["comment"])
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
                        yield AMParamStmt.from_dict(param)
                    elif param["param"] == "OF":
                        yield OFParamStmt.from_dict(param)
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

        elif isinstance(stmt, (CommentStmt, UnknownStmt, EofStmt)):
            return

        else:
            raise TypeError("Invalid statement to evaluate")


    def _define_aperture(self, d, shape, modifiers):
        aperture = None
        if shape == 'C':
            ## TODO: support %ADD10C,0.5X0.25*% and %ADD10C,0.5X0.29X0.29*%
            diameter = modifiers[0][0]
            aperture = Circle(position=None, diameter=diameter)
        elif shape == 'R':
            ## TODO: support %ADD22R,0.044X0.025X0.019*% and %ADD22R,0.044X0.025X0.024X0.013*%
            width = modifiers[0][0]
            height = modifiers[0][1]
            aperture = Rectangle(position=None, width=width, height=height)
        elif shape == 'O':
            ## TODO: support %ADD22O,0.046X0.026X0.019*% and %ADD22O,0.026X0.046X0.013X0.022*%
            width = modifiers[0][0]
            height = modifiers[0][1]
            aperture = Obround(position=None, width=width, height=height)
        elif shape == 'P':
            # FIXME: not supported yet?
            ## TODO: support %ADD17P,.040X6*% and %ADD17P,.040X6X0.0X0.019*% and %ADD17P,.040X6X15.0X0.023 X0.013*%
            raise NotImplementedError('Regular Polygon aperture not implemented')
            pass
        else:
            aperture = self.macros[shape].build(modifiers)

        self.apertures[d] = aperture

    def _evaluate_mode(self, stmt):
        if stmt.type == 'RegionMode':
            if self.region_mode == 'on' and stmt.mode == 'off':
                if self.add_debug_comment_statement:
                    self.statements.append(CommentStmt(" primitive #{0} is Region(start={1}, level_polarity={2})".format(
                        len(self.primitives), self.current_region, self.level_polarity)))
                self.primitives.append(Region(self.current_region, level_polarity=self.level_polarity))
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
            self.direction = ('clockwise' if stmt.function in ('G02', 'G2') else 'counterclockwise')

        if stmt.op:
            self.op = stmt.op

        if self.op == "D01":
            if self.region_mode == 'on':
                if self.current_region is None:
                    self.current_region = [(self.x, self.y), ]
                self.current_region.append((x, y,))
            else:
                start = (self.x, self.y)
                end = (x, y)
                #width = self.apertures[self.aperture].stroke_width
                if self.interpolation == 'linear':

                    if self.add_debug_comment_statement:
                        self.statements.append(CommentStmt(" primitive #{4} is Line(start={0}, end={1}, aperture={2}, level_polarity={3})".format(
                            start, end, self.aperture, self.level_polarity, len(self.primitives))))

                    self.primitives.append(Line(start, end, self.apertures[self.aperture], level_polarity=self.level_polarity))
                else:
                    center = (start[0] + stmt.i, start[1] + stmt.j)

                    if self.add_debug_comment_statement:
                        self.statements.append(CommentStmt(" primitive #{4} is Arc(start={0}, end={1}, center={5}, direction={6}, aperture={2}, level_polarity={3})".format(
                            start, end, self.aperture, self.level_polarity, len(self.primitives), center, self.direction)))

                    self.primitives.append(Arc(start, end, center, self.direction, self.apertures[self.aperture], level_polarity=self.level_polarity))

        elif self.op == "D02":
            pass

        elif self.op == "D03":

            primitive = copy.deepcopy(self.apertures[self.aperture])
            # XXX: temporary fix because there are no primitives for Macros and Polygon
            if primitive is None:
                raise Exception("Undefined aperture %d used" % self.aperture)
            else:
                # XXX: just to make it easy to spot
                if isinstance(primitive, type([])):
                    print(primitive[0].to_gerber())     # heu... to_gerber is not a method of primitives?
                else:
                    primitive.position = (x, y)
                    primitive.level_polarity = self.level_polarity

                    if self.add_debug_comment_statement:
                        self.statements.append(CommentStmt(" primitive #{0} is aperture={1}, level_polarity={2}, position={3}".format(
                            len(self.primitives), self.aperture, self.level_polarity, primitive.position)))

                    self.primitives.append(primitive)

        self.x, self.y = x, y

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
