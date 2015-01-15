#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>

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
Excellon File module
====================
**Excellon file classes**

This module provides Excellon file classes and parsing utilities
"""


from .excellon_statements import *
from .cam import CamFile, FileSettings
from .primitives import Drill
import math
import re

def read(filename):
    """ Read data from filename and return an ExcellonFile
    Parameters
        ----------
    filename : string
        Filename of file to parse

    Returns
    -------
    file : :class:`gerber.excellon.ExcellonFile`
        An ExcellonFile created from the specified file.

    """
    return ExcellonParser(None).parse(filename)


class ExcellonFile(CamFile):
    """ A class representing a single excellon file

    The ExcellonFile class represents a single excellon file.

    Parameters
    ----------
    tools : list
        list of gerber file statements

    hits : list of tuples
        list of drill hits as (<Tool>, (x, y))
    settings : dict
        Dictionary of gerber file settings

    filename : string
        Filename of the source gerber file

    Attributes
    ----------
    units : string
        either 'inch' or 'metric'.

    """
    def __init__(self, statements, tools, hits, settings, filename=None):
        super(ExcellonFile, self).__init__(statements=statements,
                                           settings=settings,
                                           filename=filename)
        self.tools = tools
        self.hits = hits
        self.primitives = [Drill(position, tool.diameter)
                           for tool, position in self.hits]

    @property
    def bounds(self):
        xmin = ymin = 100000000000
        xmax = ymax = -100000000000
        for tool, position in self.hits:
            radius = tool.diameter / 2.
            x = position[0]
            y = position[1]
            xmin = min(x - radius, xmin)
            xmax = max(x + radius, xmax)
            ymin = min(y - radius, ymin)
            ymax = max(y + radius, ymax)
        return ((xmin, xmax), (ymin, ymax))

    def report(self):
        """ Print drill report
        """
        pass


    def write(self, filename):
        with open(filename, 'w') as f:
            for statement in self.statements:
                f.write(statement.to_excellon(self.settings) + '\n')


class ExcellonParser(object):
    """ Excellon File Parser

    Parameters
    ----------
    settings : FileSettings or dict-like
        Excellon file settings to use when interpreting the excellon file.
    """
    def __init__(self, settings=None):
        self.notation = 'absolute'
        self.units = 'inch'
        self.zero_suppression = 'leading'
        self.format = (2, 4)
        self.state = 'INIT'
        self.statements = []
        self.tools = {}
        self.hits = []
        self.active_tool = None
        self.pos = [0., 0.]
        if settings is not None:
            self.units = settings.units
            self.zero_suppression = settings.zero_suppression
            self.notation = settings.notation
            self.format = settings.format


    @property
    def coordinates(self):
        return [(stmt.x, stmt.y) for stmt in self.statements if isinstance(stmt, CoordinateStmt)]

    @property
    def bounds(self):
        xmin = ymin = 100000000000
        xmax = ymax = -100000000000
        for x, y in self.coordinates:
            if x is not None:
                xmin = x if x < xmin else xmin
                xmax = x if x > xmax else xmax
            if y is not None:
                ymin = y if y < ymin else ymin
                ymax = y if y > ymax else ymax
        return ((xmin, xmax), (ymin, ymax))

    @property
    def hole_sizes(self):
        return [stmt.diameter for stmt in self.statements if isinstance(stmt, ExcellonTool)]

    @property
    def hole_count(self):
        return len(self.hits)

    def parse(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                self._parse(line.strip())
        return ExcellonFile(self.statements, self.tools, self.hits,
                            self._settings(), filename)

    def _parse(self, line):
        # skip empty lines
        if not line.strip():
            return

        if line[0] == ';':
            comment_stmt = CommentStmt.from_excellon(line)
            self.statements.append(comment_stmt)

            # get format from altium comment
            if "FILE_FORMAT" in comment_stmt.comment:
                detected_format = tuple([int(x) for x in comment_stmt.comment.split('=')[1].split(":")])
                if detected_format:
                    self.format = detected_format

        elif line[:3] == 'M48':
            self.statements.append(HeaderBeginStmt())
            self.state = 'HEADER'

        elif line[0] == '%':
            self.statements.append(RewindStopStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'

        elif line[:3] == 'M95':
            self.statements.append(HeaderEndStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'

        elif line[:3] == 'M30':
            stmt = EndOfProgramStmt.from_excellon(line)
            self.statements.append(stmt)

        elif line[:3] == 'G00':
            self.statements.append(RouteModeStmt())
            self.state = 'ROUT'

        elif line[:3] == 'G05':
            self.statements.append(DrillModeStmt())
            self.state = 'DRILL'

        elif 'INCH' in line or 'METRIC' in line:
            stmt = UnitStmt.from_excellon(line)
            self.units = stmt.units
            self.zero_suppression = stmt.zero_suppression
            self.statements.append(stmt)

        elif line[:3] == 'M71' or line [:3] == 'M72':
            stmt = MeasuringModeStmt.from_excellon(line)
            self.units = stmt.units
            self.statements.append(stmt)

        elif line[:3] == 'ICI':
            stmt = IncrementalModeStmt.from_excellon(line)
            self.notation = 'incremental' if stmt.mode == 'on' else 'absolute'
            self.statements.append(stmt)

        elif line[:3] == 'VER':
            stmt = VersionStmt.from_excellon(line)
            self.statements.append(stmt)

        elif line[:4] == 'FMAT':
            stmt = FormatStmt.from_excellon(line)
            self.statements.append(stmt)

        elif line[:4] == 'G90':
            self.statements.append(AbsoluteModeStmt())

        elif line[0] == 'T' and self.state == 'HEADER':
            tool = ExcellonTool.from_excellon(line, self._settings())
            self.tools[tool.number] = tool
            self.statements.append(tool)

        elif line[0] == 'T' and self.state != 'HEADER':
            stmt = ToolSelectionStmt.from_excellon(line)
            # T0 is used as END marker, just ignore
            if stmt.tool != 0:
                self.active_tool = self.tools[stmt.tool]
            self.statements.append(stmt)

        elif line[0] == 'R' and self.state != 'HEADER':
            stmt = RepeatHoleStmt.from_excellon(line, self._settings())
            self.statements.append(stmt)

        elif line[0] in ['X', 'Y']:
            stmt = CoordinateStmt.from_excellon(line, self._settings())
            x = stmt.x
            y = stmt.y
            self.statements.append(stmt)
            if self.notation == 'absolute':
                if x is not None:
                    self.pos[0] = x
                if y is not None:
                    self.pos[1] = y
            else:
                if x is not None:
                    self.pos[0] += x
                if y is not None:
                    self.pos[1] += y
            if self.state == 'DRILL':
                self.hits.append((self.active_tool, tuple(self.pos)))
                self.active_tool._hit()
        else:
            self.statements.append(UnknownStmt.from_excellon(line))

    def _settings(self):
        return FileSettings(units=self.units, format=self.format,
                            zero_suppression=self.zero_suppression,
                            notation=self.notation)


def detect_excellon_format(filename):
    """ Detect excellon file decimal format and zero-suppression settings.

    Parameters
    ----------
    filename : string
        Name of the file to parse. This does not check if the file is actually
        an Excellon file, so do that before calling this.

    Returns
    -------
    settings : dict
        Detected excellon file settings. Keys are
            - `format`: decimal format as tuple (<int part>, <decimal part>)
            - `zero_suppression`: zero suppression, 'leading' or 'trailing'
    """
    results = {}
    detected_zeros = None
    detected_format = None
    zs_options = ('leading', 'trailing', )
    format_options = ((2, 4), (2, 5), (3, 3),)

    # Check for obvious clues:
    p = ExcellonParser()
    p.parse(filename)

    # Get zero_suppression from a unit statement
    zero_statements = [stmt.zero_suppression for stmt in p.statements
                       if isinstance(stmt, UnitStmt)]

    # get format from altium comment
    format_comment = [stmt.comment for stmt in p.statements
                      if isinstance(stmt, CommentStmt)
                      and 'FILE_FORMAT' in stmt.comment]

    detected_format = (tuple([int(val) for val in
                             format_comment[0].split('=')[1].split(':')])
                       if len(format_comment) == 1 else None)
    detected_zeros = zero_statements[0] if len(zero_statements) == 1 else None

    # Bail out here if possible
    if detected_format is not None and detected_zeros is not None:
        return {'format': detected_format, 'zero_suppression': detected_zeros}

    # Only look at remaining options
    if detected_format is not None:
        format_options = (detected_format,)
    if detected_zeros is not None:
        zs_options = (detected_zeros,)

    # Brute force all remaining options, and pick the best looking one...
    for zs in zs_options:
        for fmt in format_options:
            key = (fmt, zs)
            settings = FileSettings(zero_suppression=zs, format=fmt)
            try:
                p = ExcellonParser(settings)
                p.parse(filename)
                size = tuple([t[1] - t[0] for t in p.bounds])
                hole_area = 0.0
                for hit in p.hits:
                    tool = hit[0]
                    hole_area += math.pow(math.pi * tool.diameter / 2., 2)
                results[key] = (size, p.hole_count, hole_area)
            except:
                pass

    # See if any of the dimensions are left with only a single option
    formats = set(key[0] for key in results.iterkeys())
    zeros = set(key[1] for key in results.iterkeys())
    if len(formats) == 1:
        detected_format = formats.pop()
    if len(zeros) == 1:
        detected_zeros = zeros.pop()

    # Bail out here if we got everything....
    if detected_format is not None and detected_zeros is not None:
        return {'format': detected_format, 'zero_suppression': detected_zeros}

    # Otherwise score each option and pick the best candidate
    else:
        scores = {}
        for key in results.keys():
            size, count, diameter = results[key]
            scores[key] = _layer_size_score(size, count, diameter)
        minscore = min(scores.values())
        for key in scores.iterkeys():
            if scores[key] == minscore:
                return {'format': key[0], 'zero_suppression': key[1]}


def _layer_size_score(size, hole_count, hole_area):
    """ Heuristic used for determining the correct file number interpretation.
    Lower is better.
    """
    board_area = size[0] * size[1]
    hole_percentage = hole_area / board_area
    hole_score = (hole_percentage - 0.25) ** 2
    size_score = (board_area - 8) **2
    return hole_score * size_score
