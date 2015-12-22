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

import math
import operator

try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO

from .excellon_statements import *
from .cam import CamFile, FileSettings
from .primitives import Drill
from .utils import inch, metric


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
    # File object should use settings from source file by default.
    with open(filename, 'rU') as f:
        data = f.read()
    settings = FileSettings(**detect_excellon_format(data))
    return ExcellonParser(settings).parse(filename)


def loads(data):
    """ Read data from string and return an ExcellonFile
    Parameters
    ----------
    data : string
        string containing Excellon file contents

    Returns
    -------
    file : :class:`gerber.excellon.ExcellonFile`
        An ExcellonFile created from the specified file.

    """
    # File object should use settings from source file by default.
    settings = FileSettings(**detect_excellon_format(data))
    return ExcellonParser(settings).parse_raw(data)


class DrillHit(object):
    def __init__(self, tool, position):
        self.tool = tool
        self.position = position

    def to_inch(self):
        if self.tool.units == 'metric':
            self.tool.to_inch()
            self.position = tuple(map(inch, self.position))

    def to_metric(self):
        if self.tool.units == 'inch':
            self.tool.to_metric()
            self.position = tuple(map(metric, self.position))


class ExcellonFile(CamFile):
    """ A class representing a single excellon file

    The ExcellonFile class represents a single excellon file.

    http://www.excellon.com/manuals/program.htm
    (archived version at https://web.archive.org/web/20150920001043/http://www.excellon.com/manuals/program.htm)

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

    @property
    def primitives(self):
        return [Drill(hit.position, hit.tool.diameter,units=self.settings.units) for hit in self.hits]


    @property
    def bounds(self):
        xmin = ymin = 100000000000
        xmax = ymax = -100000000000
        for hit in self.hits:
            radius = hit.tool.diameter / 2.
            x, y = hit.position
            xmin = min(x - radius, xmin)
            xmax = max(x + radius, xmax)
            ymin = min(y - radius, ymin)
            ymax = max(y + radius, ymax)
        return ((xmin, xmax), (ymin, ymax))

    def report(self, filename=None):
        """ Print or save drill report
        """
        if self.settings.units == 'inch':
            toolfmt = '  T{:0>2d}      {:%d.%df}     {: >3d}     {:f}in.\n' % self.settings.format
        else:
            toolfmt = '  T{:0>2d}      {:%d.%df}     {: >3d}     {:f}mm\n' % self.settings.format
        rprt = '=====================\nExcellon Drill Report\n=====================\n'
        if self.filename is not None:
            rprt += 'NC Drill File: %s\n\n' % self.filename
        rprt += 'Drill File Info:\n----------------\n'
        rprt += ('  Data Mode         %s\n' % 'Absolute'
                 if self.settings.notation == 'absolute' else 'Incremental')
        rprt += ('  Units             %s\n' % 'Inches'
                 if self.settings.units == 'inch' else 'Millimeters')
        rprt += '\nTool List:\n----------\n\n'
        rprt += '  Code      Size     Hits    Path Length\n'
        rprt += '  --------------------------------------\n'
        for tool in iter(self.tools.values()):
            rprt += toolfmt.format(tool.number, tool.diameter, tool.hit_count, self.path_length(tool.number))
        if filename is not None:
            with open(filename, 'w') as f:
                f.write(rprt)
        return rprt

    def write(self, filename=None):
        filename = filename if filename is not None else self.filename
        with open(filename, 'w') as f:

            # Copy the header verbatim
            for statement in self.statements:
                if not isinstance(statement, ToolSelectionStmt):
                    f.write(statement.to_excellon(self.settings) + '\n')
                else:
                    break

            # Write out coordinates for drill hits by tool
            for tool in iter(self.tools.values()):
                f.write(ToolSelectionStmt(tool.number).to_excellon(self.settings) + '\n')
                for hit in self.hits:
                    if hit.tool.number == tool.number:
                        f.write(CoordinateStmt(*hit.position).to_excellon(self.settings) + '\n')
            f.write(EndOfProgramStmt().to_excellon() + '\n')

    def to_inch(self):
        """
        Convert units to inches
        """
        if self.units != 'inch':
            self.units = 'inch'
            for statement in self.statements:
                statement.to_inch()
            for tool in iter(self.tools.values()):
                tool.to_inch()
            for primitive in self.primitives:
                primitive.to_inch()
            for hit in self.hits:
                hit.position = tuple(map(inch, hit,position))


    def to_metric(self):
        """  Convert units to metric
        """
        if self.units != 'metric':
            self.units = 'metric'
            for statement in self.statements:
                statement.to_metric()
            for tool in iter(self.tools.values()):
                tool.to_metric()
            for primitive in self.primitives:
                primitive.to_metric()
            for hit in self.hits:
                hit.position = tuple(map(metric, hit.position))

    def offset(self, x_offset=0, y_offset=0):
        for statement in self.statements:
            statement.offset(x_offset, y_offset)
        for primitive in self.primitives:
            primitive.offset(x_offset, y_offset)
        for hit in self. hits:
            hit.position = tuple(map(operator.add, hit.position, (x_offset, y_offset)))

    def path_length(self, tool_number=None):
        """ Return the path length for a given tool
        """
        lengths = {}
        positions = {}
        for hit in self.hits:
            tool = hit.tool
            num = tool.number
            positions[num] = (0, 0) if positions.get(num) is None else positions[num]
            lengths[num] = 0.0 if lengths.get(num) is None else lengths[num]
            lengths[num] = lengths[num] + math.hypot(*tuple(map(operator.sub, positions[num], hit.position)))
            positions[num] = hit.position

        if tool_number is None:
            return lengths
        else:
            return lengths.get(tool_number)

    def hit_count(self, tool_number=None):
            counts = {}
            for tool in iter(self.tools.values()):
                counts[tool.number] = tool.hit_count
            if tool_number is None:
                return counts
            else:
                return counts.get(tool_number)

    def update_tool(self, tool_number, **kwargs):
        """ Change parameters of a tool
        """
        if kwargs.get('feed_rate') is not None:
            self.tools[tool_number].feed_rate = kwargs.get('feed_rate')
        if kwargs.get('retract_rate') is not None:
            self.tools[tool_number].retract_rate = kwargs.get('retract_rate')
        if kwargs.get('rpm') is not None:
            self.tools[tool_number].rpm = kwargs.get('rpm')
        if kwargs.get('diameter') is not None:
            self.tools[tool_number].diameter = kwargs.get('diameter')
        if kwargs.get('max_hit_count') is not None:
            self.tools[tool_number].max_hit_count = kwargs.get('max_hit_count')
        if kwargs.get('depth_offset') is not None:
            self.tools[tool_number].depth_offset = kwargs.get('depth_offset')
        # Update drill hits
        newtool = self.tools[tool_number]
        for hit in self.hits:
            if hit.tool.number == newtool.number:
                hit.tool = newtool



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
        self.zeros = 'leading'
        self.format = (2, 4)
        self.state = 'INIT'
        self.statements = []
        self.tools = {}
        self.hits = []
        self.active_tool = None
        self.pos = [0., 0.]
        if settings is not None:
            self.units = settings.units
            self.zeros = settings.zeros
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
        with open(filename, 'rU') as f:
            data = f.read()
        return self.parse_raw(data, filename)

    def parse_raw(self, data, filename=None):
        for line in StringIO(data):
            self._parse_line(line.strip())
        for stmt in self.statements:
            stmt.units = self.units
        return ExcellonFile(self.statements, self.tools, self.hits,
                            self._settings(), filename)

    def _parse_line(self, line):
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
            elif self.state == 'INIT':
                self.state = 'HEADER'

        elif line[:3] == 'M95':
            self.statements.append(HeaderEndStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'

        elif line[:3] == 'M15':
            self.statements.append(ZAxisRoutPositionStmt())

        elif line[:3] == 'M16':
            self.statements.append(RetractWithClampingStmt())

        elif line[:3] == 'M17':
            self.statements.append(RetractWithoutClampingStmt())

        elif line[:3] == 'M30':
            stmt = EndOfProgramStmt.from_excellon(line, self._settings())
            self.statements.append(stmt)

        elif line[:3] == 'G00':
            self.statements.append(RouteModeStmt())
            self.state = 'ROUT'

            stmt = CoordinateStmt.from_excellon(line[3:], self._settings())
            stmt.mode = self.state

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

        elif line[:3] == 'G01':
            self.statements.append(RouteModeStmt())
            self.state = 'LINEAR'

            stmt = CoordinateStmt.from_excellon(line[3:], self._settings())
            stmt.mode = self.state

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

        elif line[:3] == 'G05':
            self.statements.append(DrillModeStmt())
            self.state = 'DRILL'

        elif 'INCH' in line or 'METRIC' in line:
            stmt = UnitStmt.from_excellon(line)
            self.units = stmt.units
            self.zeros = stmt.zeros
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

        elif line[:3] == 'G40':
            self.statements.append(CutterCompensationOffStmt())

        elif line[:3] == 'G41':
            self.statements.append(CutterCompensationLeftStmt())

        elif line[:3] == 'G42':
            self.statements.append(CutterCompensationRightStmt())

        elif line[:3] == 'G90':
            self.statements.append(AbsoluteModeStmt())
            self.notation = 'absolute'

        elif line[0] == 'F':
            infeed_rate_stmt = ZAxisInfeedRateStmt.from_excellon(line)
            self.statements.append(infeed_rate_stmt)

        elif line[0] == 'T' and self.state == 'HEADER':
            tool = ExcellonTool.from_excellon(line, self._settings())
            self.tools[tool.number] = tool
            self.statements.append(tool)

        elif line[0] == 'T' and self.state != 'HEADER':
            stmt = ToolSelectionStmt.from_excellon(line)
            self.statements.append(stmt)

            # T0 is used as END marker, just ignore
            if stmt.tool != 0:
                # FIXME: for weird files with no tools defined, original calc from gerbv
                if stmt.tool not in self.tools:
                    if self._settings().units == "inch":
                        diameter = (16 + 8 * stmt.tool) / 1000.0;
                    else:
                        diameter = metric((16 + 8 * stmt.tool) / 1000.0);

                    tool = ExcellonTool(self._settings(), number=stmt.tool, diameter=diameter)
                    self.tools[tool.number] = tool

                    # FIXME: need to add this tool definition inside header to make sure it is properly written
                    for i, s in enumerate(self.statements):
                        if isinstance(s, ToolSelectionStmt) or isinstance(s, ExcellonTool):
                            self.statements.insert(i, tool)
                            break

                self.active_tool = self.tools[stmt.tool]

        elif line[0] == 'R' and self.state != 'HEADER':
            stmt = RepeatHoleStmt.from_excellon(line, self._settings())
            self.statements.append(stmt)
            for i in range(stmt.count):
                self.pos[0] += stmt.xdelta if stmt.xdelta is not None else 0
                self.pos[1] += stmt.ydelta if stmt.ydelta is not None else 0
                self.hits.append(DrillHit(self.active_tool, tuple(self.pos)))
                self.active_tool._hit()

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
                self.hits.append(DrillHit(self.active_tool, tuple(self.pos)))
                self.active_tool._hit()
        else:
            self.statements.append(UnknownStmt.from_excellon(line))

    def _settings(self):
        return FileSettings(units=self.units, format=self.format,
                            zeros=self.zeros, notation=self.notation)


def detect_excellon_format(data=None, filename=None):
    """ Detect excellon file decimal format and zero-suppression settings.

    Parameters
    ----------
    data : string
        String containing contents of Excellon file.

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
    zeros_options = ('leading', 'trailing', )
    format_options = ((2, 4), (2, 5), (3, 3),)

    if data is None and filename is None:
        raise ValueError('Either data or filename arguments must be provided')
    if data is None:
        with open(filename, 'rU') as f:
            data = f.read()

    # Check for obvious clues:
    p = ExcellonParser()
    p.parse_raw(data)

    # Get zero_suppression from a unit statement
    zero_statements = [stmt.zeros for stmt in p.statements
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
        return {'format': detected_format, 'zeros': detected_zeros}

    # Only look at remaining options
    if detected_format is not None:
        format_options = (detected_format,)
    if detected_zeros is not None:
        zeros_options = (detected_zeros,)

    # Brute force all remaining options, and pick the best looking one...
    for zeros in zeros_options:
        for fmt in format_options:
            key = (fmt, zeros)
            settings = FileSettings(zeros=zeros, format=fmt)
            try:
                p = ExcellonParser(settings)
                p.parse_raw(data)
                size = tuple([t[0] - t[1] for t in p.bounds])
                hole_area = 0.0
                for hit in p.hits:
                    tool = hit.tool
                    hole_area += math.pow(math.pi * tool.diameter / 2., 2)
                results[key] = (size, p.hole_count, hole_area)
            except:
                pass

    # See if any of the dimensions are left with only a single option
    formats = set(key[0] for key in iter(results.keys()))
    zeros = set(key[1] for key in iter(results.keys()))
    if len(formats) == 1:
        detected_format = formats.pop()
    if len(zeros) == 1:
        detected_zeros = zeros.pop()

    # Bail out here if we got everything....
    if detected_format is not None and detected_zeros is not None:
        return {'format': detected_format, 'zeros': detected_zeros}

    # Otherwise score each option and pick the best candidate
    else:
        scores = {}
        for key in results.keys():
            size, count, diameter = results[key]
            scores[key] = _layer_size_score(size, count, diameter)
        minscore = min(scores.values())
        for key in iter(scores.keys()):
            if scores[key] == minscore:
                return {'format': key[0], 'zeros': key[1]}


def _layer_size_score(size, hole_count, hole_area):
    """ Heuristic used for determining the correct file number interpretation.
    Lower is better.
    """
    board_area = size[0] * size[1]
    hole_percentage = hole_area / board_area
    hole_score = (hole_percentage - 0.25) ** 2
    size_score = (board_area - 8) **2
    return hole_score * size_score
