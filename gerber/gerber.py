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
"""
Gerber File module
==================
**Gerber File module**

This module provides an RS-274-X class and parser
"""


import re
import json
from .gerber_statements import *
from .cam import CamFile, FileSettings




def read(filename):
    """ Read data from filename and return a GerberFile
    """
    return GerberParser().parse(filename)


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
    def __init__(self, statements, settings, filename=None):
        super(GerberFile, self).__init__(statements, settings, filename)

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
        xbounds = [0.0, 0.0]
        ybounds = [0.0, 0.0]
        for stmt in [stmt for stmt in self.statements
                     if isinstance(stmt, CoordStmt)]:
            if stmt.x is not None and stmt.x < xbounds[0]:
                xbounds[0] = stmt.x
            if stmt.x is not None and stmt.x > xbounds[1]:
                xbounds[1] = stmt.x
            if stmt.i is not None and stmt.i < xbounds[0]:
                xbounds[0] = stmt.i
            if stmt.i is not None and stmt.i > xbounds[1]:
                xbounds[1] = stmt.i
            if stmt.y is not None and stmt.y < ybounds[0]:
                ybounds[0] = stmt.y
            if stmt.y is not None and stmt.y > ybounds[1]:
                ybounds[1] = stmt.y
            if stmt.j is not None and stmt.j < ybounds[0]:
                ybounds[0] = stmt.j
            if stmt.j is not None and stmt.j > ybounds[1]:
                ybounds[1] = stmt.j
        return (xbounds, ybounds)

    def write(self, filename):
        """ Write data out to a gerber file
        """
        with open(filename, 'w') as f:
            for statement in self.statements:
                f.write(statement.to_gerber())

    def render(self, ctx, filename=None):
        """ Generate image of layer.
        """
        ctx.set_bounds(self.bounds)
        for statement in self.statements:
            ctx.evaluate(statement)
        if filename is not None:
            ctx.dump(filename)


class GerberParser(object):
    """ GerberParser
    """
    NUMBER = r"[\+-]?\d+"
    DECIMAL = r"[\+-]?\d+([.]?\d+)?"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"
    NAME = "[a-zA-Z_$][a-zA-Z_$0-9]+"
    FUNCTION = r"G\d{2}"

    COORD_OP = r"D[0]?[123]"

    FS = r"(?P<param>FS)(?P<zero>(L|T))?(?P<notation>(A|I))X(?P<x>[0-7][0-7])Y(?P<y>[0-7][0-7])"
    MO = r"(?P<param>MO)(?P<mo>(MM|IN))"
    IP = r"(?P<param>IP)(?P<ip>(POS|NEG))"
    LP = r"(?P<param>LP)(?P<lp>(D|C))"
    AD_CIRCLE = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>C)[,](?P<modifiers>[^,]*)"
    AD_RECT = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>R)[,](?P<modifiers>[^,]*)"
    AD_OBROUND = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>O)[,](?P<modifiers>[^,]*)"
    AD_POLY = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>P)[,](?P<modifiers>[^,]*)"
    AD_MACRO = r"(?P<param>AD)D(?P<d>\d+)+(?P<shape>{name})[,](?P<modifiers>[^,]*)".format(name=NAME)
    AM = r"(?P<param>AM)(?P<name>{name})\*(?P<macro>.*)".format(name=NAME)

    # begin deprecated
    OF = r"(?P<param>OF)(A(?P<a>{decimal}))?(B(?P<b>{decimal}))?".format(decimal=DECIMAL)
    IN = r"(?P<param>IN)(?P<name>.*)"
    LN = r"(?P<param>LN)(?P<name>.*)"
    # end deprecated

    PARAMS = (FS, MO, IP, LP, AD_CIRCLE, AD_RECT, AD_OBROUND, AD_MACRO, AD_POLY, AM, OF, IN, LN)
    PARAM_STMT = [re.compile(r"%{0}\*%".format(p)) for p in PARAMS]

    COORD_STMT = re.compile((
        r"(?P<function>{function})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, function=FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(G54)?D(?P<d>\d+)\*")

    COMMENT_STMT = re.compile(r"G04(?P<comment>[^*]*)(\*)?")

    EOF_STMT = re.compile(r"(?P<eof>M02)\*")

    REGION_MODE_STMT = re.compile(r'(?P<mode>G3[67])\*')
    QUAD_MODE_STMT = re.compile(r'(?P<mode>G7[45])\*')

    def __init__(self):
        self.settings = FileSettings()
        self.statements = []

    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        for stmt in self._parse(data):
            self.statements.append(stmt)

        return GerberFile(self.statements, self.settings, filename)

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
                (mode, r) = self._match_one(self.REGION_MODE_STMT, line)
                if mode:
                    yield RegionModeStmt.from_gerber(line)
                    line = r
                    did_something = True
                    continue

                # Quadrant Mode
                (mode, r) = self._match_one(self.QUAD_MODE_STMT, line)
                if mode:
                    yield QuadrantModeStmt.from_gerber(line)
                    line = r
                    did_something = True
                    continue

                # coord
                (coord, r) = self._match_one(self.COORD_STMT, line)
                if coord:
                    yield CoordStmt.from_dict(coord, self.settings)
                    line = r
                    did_something = True
                    continue

                # aperture selection
                (aperture, r) = self._match_one(self.APERTURE_STMT, line)
                if aperture:
                    yield ApertureStmt(**aperture)

                    did_something = True
                    line = r
                    continue

                # comment
                (comment, r) = self._match_one(self.COMMENT_STMT, line)
                if comment:
                    yield CommentStmt(comment["comment"])
                    did_something = True
                    line = r
                    continue

                # parameter
                (param, r) = self._match_one_from_many(self.PARAM_STMT, line)
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
                    elif param["param"] == "IP":
                        yield IPParamStmt.from_dict(param)
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
                    else:
                        yield UnknownStmt(line)
                    did_something = True
                    line = r
                    continue

                # eof
                (eof, r) = self._match_one(self.EOF_STMT, line)
                if eof:
                    yield EofStmt()
                    did_something = True
                    line = r
                    continue

                if False:
                    print self.COORD_STMT.pattern
                    print self.APERTURE_STMT.pattern
                    print self.COMMENT_STMT.pattern
                    print self.EOF_STMT.pattern
                    for i in self.PARAM_STMT:
                        print i.pattern

                if line.find('*') > 0:
                    yield UnknownStmt(line)
            oldline = line

    def _match_one(self, expr, data):
        match = expr.match(data)
        if match is None:
            return ({}, None)
        else:
            return (match.groupdict(), data[match.end(0):])

    def _match_one_from_many(self, exprs, data):
        for expr in exprs:
            match = expr.match(data)
            if match:
                return (match.groupdict(), data[match.end(0):])

        return ({}, None)
