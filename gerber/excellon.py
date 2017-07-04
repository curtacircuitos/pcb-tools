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

from .cam import CamFile, FileSettings
from .excellon_statements import *
from .excellon_tool import ExcellonToolDefinitionParser
from .primitives import Drill, Slot
from .utils import inch, metric


try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO



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

def loads(data, filename=None, settings=None, tools=None):
    """ Read data from string and return an ExcellonFile
    Parameters
    ----------
    data : string
        string containing Excellon file contents

    filename : string, optional
        string containing the filename of the data source

    tools: dict (optional)
        externally defined tools

    Returns
    -------
    file : :class:`gerber.excellon.ExcellonFile`
        An ExcellonFile created from the specified file.

    """
    # File object should use settings from source file by default.
    if not settings:
        settings = FileSettings(**detect_excellon_format(data))
    return ExcellonParser(settings, tools).parse_raw(data, filename)


class DrillHit(object):
    """Drill feature that is a single drill hole.

    Attributes
    ----------
    tool : ExcellonTool
        Tool to drill the hole. Defines the size of the hole that is generated.
    position : tuple(float, float)
        Center position of the drill.

    """
    def __init__(self, tool, position):
        self.tool = tool
        self.position = position

    def to_inch(self):
        if self.tool.settings.units == 'metric':
            self.tool.to_inch()
            self.position = tuple(map(inch, self.position))

    def to_metric(self):
        if self.tool.settings.units == 'inch':
            self.tool.to_metric()
            self.position = tuple(map(metric, self.position))

    @property
    def bounding_box(self):
        position = self.position
        radius = self.tool.diameter / 2.

        min_x = position[0] - radius
        max_x = position[0] + radius
        min_y = position[1] - radius
        max_y = position[1] + radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(operator.add, self.position, (x_offset, y_offset)))

    def __str__(self):
        return 'Hit (%f, %f) {%s}' % (self.position[0], self.position[1], self.tool)

class DrillSlot(object):
    """
    A slot is created between two points. The way the slot is created depends on the statement used to create it
    """

    TYPE_ROUT = 1
    TYPE_G85 = 2

    def __init__(self, tool, start, end, slot_type):
        self.tool = tool
        self.start = start
        self.end = end
        self.slot_type = slot_type

    def to_inch(self):
        if self.tool.settings.units == 'metric':
            self.tool.to_inch()
            self.start = tuple(map(inch, self.start))
            self.end = tuple(map(inch, self.end))

    def to_metric(self):
        if self.tool.settings.units == 'inch':
            self.tool.to_metric()
            self.start = tuple(map(metric, self.start))
            self.end = tuple(map(metric, self.end))

    @property
    def bounding_box(self):
        start = self.start
        end = self.end
        radius = self.tool.diameter / 2.
        min_x = min(start[0], end[0]) - radius
        max_x = max(start[0], end[0]) + radius
        min_y = min(start[1], end[1]) - radius
        max_y = max(start[1], end[1]) + radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.start = tuple(map(operator.add, self.start, (x_offset, y_offset)))
        self.end = tuple(map(operator.add, self.end, (x_offset, y_offset)))


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
        """
        Gets the primitives. Note that unlike Gerber, this generates new objects
        """
        primitives = []
        for hit in self.hits:
            if isinstance(hit, DrillHit):
                primitives.append(Drill(hit.position, hit.tool.diameter,
                                        units=self.settings.units))
            elif isinstance(hit, DrillSlot):
                primitives.append(Slot(hit.start, hit.end, hit.tool.diameter,
                                       units=self.settings.units))
            else:
                raise ValueError('Unknown hit type')
        return primitives

    @property
    def bounding_box(self):
        xmin = ymin = 100000000000
        xmax = ymax = -100000000000
        for hit in self.hits:
            bbox = hit.bounding_box
            xmin = min(bbox[0][0], xmin)
            xmax = max(bbox[0][1], xmax)
            ymin = min(bbox[1][0], ymin)
            ymax = max(bbox[1][1], ymax)
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
            rprt += toolfmt.format(tool.number, tool.diameter,
                                   tool.hit_count, self.path_length(tool.number))
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
                        f.write(CoordinateStmt(
                            *hit.position).to_excellon(self.settings) + '\n')
            f.write(EndOfProgramStmt().to_excellon() + '\n')

    def to_inch(self):
        """
        Convert units to inches
        """
        if self.units != 'inch':
            for statement in self.statements:
                statement.to_inch()
            for tool in iter(self.tools.values()):
                tool.to_inch()
            #for primitive in self.primitives:
            #    primitive.to_inch()
            #for hit in self.hits:
            #    hit.to_inch()
            self.units = 'inch'

    def to_metric(self):
        """  Convert units to metric
        """
        if self.units != 'metric':
            for statement in self.statements:
                statement.to_metric()
            for tool in iter(self.tools.values()):
                tool.to_metric()
            #for primitive in self.primitives:
            #    print("Converting to metric: {}".format(primitive))
            #    primitive.to_metric()
            #    print(primitive)
            for hit in self.hits:
                hit.to_metric()
            self.units = 'metric'

    def offset(self, x_offset=0, y_offset=0):
        for statement in self.statements:
            statement.offset(x_offset, y_offset)
        for primitive in self.primitives:
            primitive.offset(x_offset, y_offset)
        for hit in self. hits:
            hit.offset(x_offset, y_offset)

    def path_length(self, tool_number=None):
        """ Return the path length for a given tool
        """
        lengths = {}
        positions = {}
        for hit in self.hits:
            tool = hit.tool
            num = tool.number
            positions[num] = ((0, 0) if positions.get(num) is None
                              else positions[num])
            lengths[num] = 0.0 if lengths.get(num) is None else lengths[num]
            lengths[num] = lengths[
                num] + math.hypot(*tuple(map(operator.sub, positions[num], hit.position)))
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
    def __init__(self, settings=None, ext_tools=None):
        self.notation = 'absolute'
        self.units = 'inch'
        self.zeros = 'leading'
        self.format = (2, 4)
        self.state = 'INIT'
        self.statements = []
        self.tools = {}
        self.ext_tools = ext_tools or {}
        self.comment_tools = {}
        self.hits = []
        self.active_tool = None
        self.pos = [0., 0.]
        self.drill_down = False
        self._previous_line = ''
        # Default for plated is None, which means we don't know
        self.plated = ExcellonTool.PLATED_UNKNOWN
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
        # Prepend previous line's data...
        line = '{}{}'.format(self._previous_line, line)
        self._previous_line = ''

        # Skip empty lines
        if not line.strip():
            return

        if line[0] == ';':
            comment_stmt = CommentStmt.from_excellon(line)
            self.statements.append(comment_stmt)

            # get format from altium comment
            if "FILE_FORMAT" in comment_stmt.comment:
                detected_format = tuple(
                    [int(x) for x in comment_stmt.comment.split('=')[1].split(":")])
                if detected_format:
                    self.format = detected_format

            if "TYPE=PLATED" in comment_stmt.comment:
                self.plated = ExcellonTool.PLATED_YES

            if "TYPE=NON_PLATED" in comment_stmt.comment:
                self.plated = ExcellonTool.PLATED_NO

            if "HEADER:" in comment_stmt.comment:
                self.state = "HEADER"

            if " Holesize " in comment_stmt.comment:
                self.state = "HEADER"

                # Parse this as a hole definition
                tools = ExcellonToolDefinitionParser(self._settings()).parse_raw(comment_stmt.comment)
                if len(tools) == 1:
                    tool = tools[tools.keys()[0]]
                    self._add_comment_tool(tool)

        elif line[:3] == 'M48':
            self.statements.append(HeaderBeginStmt())
            self.state = 'HEADER'

        elif line[0] == '%':
            self.statements.append(RewindStopStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'
            elif self.state == 'INIT':
                self.state = 'HEADER'

        elif line[:3] == 'M00' and self.state == 'DRILL':
            if self.active_tool:
                cur_tool_number = self.active_tool.number
                next_tool = self._get_tool(cur_tool_number + 1)

                self.statements.append(NextToolSelectionStmt(self.active_tool, next_tool))
                self.active_tool = next_tool
            else:
                raise Exception('Invalid state exception')

        elif line[:3] == 'M95':
            self.statements.append(HeaderEndStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'

        elif line[:3] == 'M15':
            self.statements.append(ZAxisRoutPositionStmt())
            self.drill_down = True

        elif line[:3] == 'M16':
            self.statements.append(RetractWithClampingStmt())
            self.drill_down = False

        elif line[:3] == 'M17':
            self.statements.append(RetractWithoutClampingStmt())
            self.drill_down = False

        elif line[:3] == 'M30':
            stmt = EndOfProgramStmt.from_excellon(line, self._settings())
            self.statements.append(stmt)

        elif line[:3] == 'G00':
            # Coordinates may be on the next line
            if line.strip() == 'G00':
                self._previous_line = line
                return

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

            # Coordinates might be on the next line...
            if line.strip() == 'G01':
                self._previous_line = line
                return

            self.statements.append(RouteModeStmt())
            self.state = 'LINEAR'

            stmt = CoordinateStmt.from_excellon(line[3:], self._settings())
            stmt.mode = self.state

            # The start position is where we were before the rout command
            start = (self.pos[0], self.pos[1])

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

            # Our ending position
            end = (self.pos[0], self.pos[1])

            if self.drill_down:
                if not self.active_tool:
                    self.active_tool = self._get_tool(1)

                self.hits.append(DrillSlot(self.active_tool, start, end, DrillSlot.TYPE_ROUT))
                self.active_tool._hit()

        elif line[:3] == 'G05':
            self.statements.append(DrillModeStmt())
            self.drill_down = False
            self.state = 'DRILL'

        elif 'INCH' in line or 'METRIC' in line:
            stmt = UnitStmt.from_excellon(line)
            self.units = stmt.units
            self.zeros = stmt.zeros
            if stmt.format:
                self.format = stmt.format
            self.statements.append(stmt)

        elif line[:3] == 'M71' or line[:3] == 'M72':
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
            self.format = stmt.format_tuple

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
            if not ',OFF' in line and not ',ON' in line:
                tool = ExcellonTool.from_excellon(line, self._settings(), None, self.plated)
                self._merge_properties(tool)
                self.tools[tool.number] = tool
                self.statements.append(tool)
            else:
                self.statements.append(UnknownStmt.from_excellon(line))

        elif line[0] == 'T' and self.state != 'HEADER':
            stmt = ToolSelectionStmt.from_excellon(line)
            self.statements.append(stmt)

            # T0 is used as END marker, just ignore
            if stmt.tool != 0:
                tool = self._get_tool(stmt.tool)

                if not tool:
                    # FIXME: for weird files with no tools defined, original calc from gerb
                    if self._settings().units == "inch":
                        diameter = (16 + 8 * stmt.tool) / 1000.0
                    else:
                        diameter = metric((16 + 8 * stmt.tool) / 1000.0)

                    tool = ExcellonTool(
                        self._settings(), number=stmt.tool, diameter=diameter)
                    self.tools[tool.number] = tool

                    # FIXME: need to add this tool definition inside header to
                    # make sure it is properly written
                    for i, s in enumerate(self.statements):
                        if isinstance(s, ToolSelectionStmt) or isinstance(s, ExcellonTool):
                            self.statements.insert(i, tool)
                            break

                self.active_tool = tool

        elif line[0] == 'R' and self.state != 'HEADER':
            stmt = RepeatHoleStmt.from_excellon(line, self._settings())
            self.statements.append(stmt)
            for i in range(stmt.count):
                self.pos[0] += stmt.xdelta if stmt.xdelta is not None else 0
                self.pos[1] += stmt.ydelta if stmt.ydelta is not None else 0
                self.hits.append(DrillHit(self.active_tool, tuple(self.pos)))
                self.active_tool._hit()

        elif line[0] in ['X', 'Y']:
            if 'G85' in line:
                stmt = SlotStmt.from_excellon(line, self._settings())

                # I don't know if this is actually correct, but it makes sense
                # that this is where the tool would end
                x = stmt.x_end
                y = stmt.y_end

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

                if self.state == 'DRILL' or self.state == 'HEADER':
                    if not self.active_tool:
                        self.active_tool = self._get_tool(1)

                    self.hits.append(DrillSlot(self.active_tool, (stmt.x_start, stmt.y_start), (stmt.x_end, stmt.y_end), DrillSlot.TYPE_G85))
                    self.active_tool._hit()
            else:
                stmt = CoordinateStmt.from_excellon(line, self._settings())

                # We need this in case we are in rout mode
                start = (self.pos[0], self.pos[1])

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

                if self.state == 'LINEAR' and self.drill_down:
                    if not self.active_tool:
                        self.active_tool = self._get_tool(1)

                    self.hits.append(DrillSlot(self.active_tool, start, tuple(self.pos), DrillSlot.TYPE_ROUT))

                elif self.state == 'DRILL' or self.state == 'HEADER':
                    # Yes, drills in the header doesn't follow the specification, but it there are many
                    # files like this
                    if not self.active_tool:
                        self.active_tool = self._get_tool(1)

                    self.hits.append(DrillHit(self.active_tool, tuple(self.pos)))
                    self.active_tool._hit()

        else:
            self.statements.append(UnknownStmt.from_excellon(line))

    def _settings(self):
        return FileSettings(units=self.units, format=self.format,
                            zeros=self.zeros, notation=self.notation)

    def _add_comment_tool(self, tool):
        """
        Add a tool that was defined in the comments to this file.

        If we have already found this tool, then we will merge this comment tool definition into
        the information for the tool
        """

        existing = self.tools.get(tool.number)
        if existing and existing.plated == None:
            existing.plated = tool.plated

        self.comment_tools[tool.number] = tool

    def _merge_properties(self, tool):
        """
        When we have externally defined tools, merge the properties of that tool into this one

        For now, this is only plated
        """

        if tool.plated == ExcellonTool.PLATED_UNKNOWN:
            ext_tool = self.ext_tools.get(tool.number)

            if ext_tool:
                tool.plated = ext_tool.plated

    def _get_tool(self, toolid):

        tool = self.tools.get(toolid)
        if not tool:
            tool = self.comment_tools.get(toolid)
            if tool:
                tool.settings = self._settings()
                self.tools[toolid] = tool

        if not tool:
            tool = self.ext_tools.get(toolid)
            if tool:
                tool.settings = self._settings()
                self.tools[toolid] = tool

        return tool

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
                ef = p.parse_raw(data)
                size = tuple([t[0] - t[1] for t in ef.bounding_box])
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
    if board_area == 0:
        return 0

    hole_percentage = hole_area / board_area
    hole_score = (hole_percentage - 0.25) ** 2
    size_score = (board_area - 8) ** 2
    return hole_score * size_score
