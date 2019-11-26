#!/usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
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
Excellon Statements
====================
**Excellon file statement classes**

"""

import re
import uuid
import itertools
from .utils import (parse_gerber_value, write_gerber_value, decimal_string,
                    inch, metric)


__all__ = ['ExcellonTool', 'ToolSelectionStmt', 'CoordinateStmt',
           'CommentStmt', 'HeaderBeginStmt', 'HeaderEndStmt',
           'RewindStopStmt', 'EndOfProgramStmt', 'UnitStmt',
           'IncrementalModeStmt', 'VersionStmt', 'FormatStmt', 'LinkToolStmt',
           'MeasuringModeStmt', 'RouteModeStmt', 'LinearModeStmt', 'DrillModeStmt',
           'AbsoluteModeStmt', 'RepeatHoleStmt', 'UnknownStmt',
           'ExcellonStatement', 'ZAxisRoutPositionStmt',
           'RetractWithClampingStmt', 'RetractWithoutClampingStmt',
           'CutterCompensationOffStmt', 'CutterCompensationLeftStmt',
           'CutterCompensationRightStmt', 'ZAxisInfeedRateStmt',
           'NextToolSelectionStmt', 'SlotStmt']


class ExcellonStatement(object):
    """ Excellon Statement abstract base class
    """

    @classmethod
    def from_excellon(cls, line):
        raise NotImplementedError('from_excellon must be implemented in a '
                                  'subclass')

    def __init__(self, unit='inch', id=None):
        self.units = unit
        self.id = uuid.uuid4().int if id is None else id

    def to_excellon(self, settings=None):
        raise NotImplementedError('to_excellon must be implemented in a '
                                  'subclass')

    def to_inch(self):
        self.units = 'inch'

    def to_metric(self):
        self.units = 'metric'

    def offset(self, x_offset=0, y_offset=0):
        pass

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ExcellonTool(ExcellonStatement):
    """ Excellon Tool class

    Parameters
    ----------
    settings : FileSettings (dict-like)
        File-wide settings.

    kwargs : dict-like
        Tool settings from the excellon statement. Valid keys are:
            - `diameter` : Tool diameter [expressed in file units]
            - `rpm` : Tool RPM
            - `feed_rate` : Z-axis tool feed rate
            - `retract_rate` : Z-axis tool retraction rate
            - `max_hit_count` : Number of hits allowed before a tool change
            - `depth_offset` : Offset of tool depth from tip of tool.

    Attributes
    ----------
    number : integer
        Tool number from the excellon file

    diameter : float
        Tool diameter in file units

    rpm : float
        Tool RPM

    feed_rate : float
        Tool Z-axis feed rate.

    retract_rate : float
        Tool Z-axis retract rate

    depth_offset : float
        Offset of depth measurement from tip of tool

    max_hit_count : integer
        Maximum number of tool hits allowed before a tool change

    hit_count : integer
        Number of tool hits in excellon file.
    """

    PLATED_UNKNOWN = None
    PLATED_YES = 'plated'
    PLATED_NO = 'nonplated'
    PLATED_OPTIONAL = 'optional'

    @classmethod
    def from_tool(cls, tool):
        args = {}

        args['depth_offset'] = tool.depth_offset
        args['diameter'] = tool.diameter
        args['feed_rate'] = tool.feed_rate
        args['max_hit_count'] = tool.max_hit_count
        args['number'] = tool.number
        args['plated'] = tool.plated
        args['retract_rate'] = tool.retract_rate
        args['rpm'] = tool.rpm

        return cls(None, **args)

    @classmethod
    def from_excellon(cls, line, settings, id=None, plated=None):
        """ Create a Tool from an excellon file tool definition line.

        Parameters
        ----------
        line : string
            Tool definition line from an excellon file.

        settings : FileSettings (dict-like)
            Excellon file-wide settings

        Returns
        -------
        tool : Tool
            An ExcellonTool representing the tool defined in `line`
        """
        commands = pairwise(re.split('([BCFHSTZ])', line)[1:])
        args = {}
        args['id'] = id
        nformat = settings.format
        zero_suppression = settings.zero_suppression
        for cmd, val in commands:
            if cmd == 'B':
                args['retract_rate'] = parse_gerber_value(val, nformat, zero_suppression)
            elif cmd == 'C':
                args['diameter'] = parse_gerber_value(val, nformat, zero_suppression)
            elif cmd == 'F':
                args['feed_rate'] = parse_gerber_value(val, nformat, zero_suppression)
            elif cmd == 'H':
                args['max_hit_count'] = parse_gerber_value(val, nformat, zero_suppression)
            elif cmd == 'S':
                args['rpm'] = 1000 * parse_gerber_value(val, nformat, zero_suppression)
            elif cmd == 'T':
                args['number'] = int(val)
            elif cmd == 'Z':
                args['depth_offset'] = parse_gerber_value(val, nformat, zero_suppression)

        if plated != ExcellonTool.PLATED_UNKNOWN:
            # Sometimees we can can parse the plating status
            args['plated'] = plated
        return cls(settings, **args)

    @classmethod
    def from_dict(cls, settings, tool_dict):
        """ Create an ExcellonTool from a dict.

        Parameters
        ----------
        settings : FileSettings (dict-like)
            Excellon File-wide settings

        tool_dict : dict
            Excellon tool parameters as a dict

        Returns
        -------
        tool : ExcellonTool
            An ExcellonTool initialized with the parameters in tool_dict.
        """
        return cls(settings, **tool_dict)

    def __init__(self, settings, **kwargs):
        if kwargs.get('id') is not None:
            super(ExcellonTool, self).__init__(id=kwargs.get('id'))
        self.settings = settings
        self.number = kwargs.get('number')
        self.feed_rate = kwargs.get('feed_rate')
        self.retract_rate = kwargs.get('retract_rate')
        self.rpm = kwargs.get('rpm')
        self.diameter = kwargs.get('diameter')
        self.max_hit_count = kwargs.get('max_hit_count')
        self.depth_offset = kwargs.get('depth_offset')
        self.plated = kwargs.get('plated')

        self.hit_count = 0

    def to_excellon(self, settings=None):
        if self.settings and not settings:
            settings = self.settings
        fmt = settings.format
        zs = settings.zero_suppression
        stmt = 'T%02d' % self.number
        if self.retract_rate is not None:
            stmt += 'B%s' % write_gerber_value(self.retract_rate, fmt, zs)
        if self.feed_rate is not None:
            stmt += 'F%s' % write_gerber_value(self.feed_rate, fmt, zs)
        if self.max_hit_count is not None:
            stmt += 'H%s' % write_gerber_value(self.max_hit_count, fmt, zs)
        if self.rpm is not None:
            if self.rpm < 100000.:
                stmt += 'S%s' % write_gerber_value(self.rpm / 1000., fmt, zs)
            else:
                stmt += 'S%g' % (self.rpm / 1000.)
        if self.diameter is not None:
            stmt += 'C%s' % decimal_string(self.diameter, fmt[1], True)
        if self.depth_offset is not None:
            stmt += 'Z%s' % write_gerber_value(self.depth_offset, fmt, zs)
        return stmt

    def to_inch(self):
        if self.settings.units != 'inch':
            self.settings.units = 'inch'
            if self.diameter is not None:
                self.diameter = inch(self.diameter)

    def to_metric(self):
        if self.settings.units != 'metric':
            self.settings.units = 'metric'
            if self.diameter is not None:
                self.diameter = metric(self.diameter)

    def _hit(self):
        self.hit_count += 1

    def equivalent(self, other):
        """
        Is the other tool equal to this, ignoring the tool number, and other file specified properties
        """

        if type(self) != type(other):
            return False

        return (self.diameter == other.diameter
            and self.feed_rate == other.feed_rate
            and self.retract_rate == other.retract_rate
            and self.rpm == other.rpm
            and self.depth_offset == other.depth_offset
            and self.max_hit_count == other.max_hit_count
            and self.plated == other.plated
            and self.settings.units == other.settings.units)

    def __repr__(self):
        unit = 'in.' if self.settings.units == 'inch' else 'mm'
        fmtstr = '<ExcellonTool %%02d: %%%d.%dg%%s dia.>' % self.settings.format
        return fmtstr % (self.number, self.diameter, unit)


class ToolSelectionStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        """ Create a ToolSelectionStmt from an excellon file line.

        Parameters
        ----------
        line : string
            Line from an Excellon file

        Returns
        -------
        tool_statement : ToolSelectionStmt
            ToolSelectionStmt representation of `line.`
        """
        line = line[1:]
        compensation_index = None

        # up to 3 characters for tool number (Frizting uses that)
        if len(line) <= 3:
            tool = int(line)
        else:
            tool = int(line[:2])
            compensation_index = int(line[2:])

        return cls(tool, compensation_index, **kwargs)

    def __init__(self, tool, compensation_index=None, **kwargs):
        super(ToolSelectionStmt, self).__init__(**kwargs)
        tool = int(tool)
        compensation_index = (int(compensation_index) if compensation_index
                              is not None else None)
        self.tool = tool
        self.compensation_index = compensation_index

    def to_excellon(self, settings=None):
        stmt = 'T%02d' % self.tool
        if self.compensation_index is not None:
            stmt += '%02d' % self.compensation_index
        return stmt

class NextToolSelectionStmt(ExcellonStatement):

    # TODO the statement exists outside of the context of the file,
    # so it is imposible to know that it is really the next tool

    def __init__(self, cur_tool, next_tool, **kwargs):
        """
        Select the next tool in the wheel.
        Parameters
        ----------
        cur_tool : the tool that is currently selected
        next_tool : the that that is now selected
        """
        super(NextToolSelectionStmt, self).__init__(**kwargs)

        self.cur_tool = cur_tool
        self.next_tool = next_tool

    def to_excellon(self, settings=None):
        stmt = 'M00'
        return stmt

class ZAxisInfeedRateStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        """ Create a ZAxisInfeedRate from an excellon file line.

        Parameters
        ----------
        line : string
            Line from an Excellon file

        Returns
        -------
        z_axis_infeed_rate : ToolSelectionStmt
            ToolSelectionStmt representation of `line.`
        """
        rate = int(line[1:])

        return cls(rate, **kwargs)

    def __init__(self, rate, **kwargs):
        super(ZAxisInfeedRateStmt, self).__init__(**kwargs)
        self.rate = rate

    def to_excellon(self, settings=None):
        return 'F%02d' % self.rate


class CoordinateStmt(ExcellonStatement):

    @classmethod
    def from_point(cls, point, mode=None):

        stmt = cls(point[0], point[1])
        if mode:
            stmt.mode = mode
        return stmt

    @classmethod
    def from_excellon(cls, line, settings, **kwargs):
        x_coord = None
        y_coord = None
        if line[0] == 'X':
            splitline = line.strip('X').split('Y')
            x_coord = parse_gerber_value(splitline[0], settings.format,
                                         settings.zero_suppression)
            if len(splitline) == 2:
                y_coord = parse_gerber_value(splitline[1], settings.format,
                                             settings.zero_suppression)
        else:
            y_coord = parse_gerber_value(line.strip(' Y'), settings.format,
                                         settings.zero_suppression)
        c = cls(x_coord, y_coord, **kwargs)
        c.units = settings.units
        return c

    def __init__(self, x=None, y=None, **kwargs):
        super(CoordinateStmt, self).__init__(**kwargs)
        self.x = x
        self.y = y
        self.mode = None

    def to_excellon(self, settings):
        stmt = ''
        if self.mode == "ROUT":
            stmt += "G00"
        if self.mode == "LINEAR":
            stmt += "G01"
        if self.x is not None:
            stmt += 'X%s' % write_gerber_value(self.x, settings.format,
                                               settings.zero_suppression)
        if self.y is not None:
            stmt += 'Y%s' % write_gerber_value(self.y, settings.format,
                                               settings.zero_suppression)
        return stmt

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.x is not None:
                self.x = inch(self.x)
            if self.y is not None:
                self.y = inch(self.y)

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.x is not None:
                self.x = metric(self.x)
            if self.y is not None:
                self.y = metric(self.y)

    def offset(self, x_offset=0, y_offset=0):
        if self.x is not None:
            self.x += x_offset
        if self.y is not None:
            self.y += y_offset

    def __str__(self):
        coord_str = ''
        if self.x is not None:
            coord_str += 'X: %g ' % self.x
        if self.y is not None:
            coord_str += 'Y: %g ' % self.y

        return '<Coordinate Statement: %s>' % coord_str


class RepeatHoleStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, settings, **kwargs):
        match = re.compile(r'R(?P<rcount>[0-9]*)X?(?P<xdelta>[+\-]?\d*\.?\d*)?Y?'
                           '(?P<ydelta>[+\-]?\d*\.?\d*)?').match(line)
        stmt = match.groupdict()
        count = int(stmt['rcount'])
        xdelta = (parse_gerber_value(stmt['xdelta'], settings.format,
                                     settings.zero_suppression)
                  if stmt['xdelta'] is not '' else None)
        ydelta = (parse_gerber_value(stmt['ydelta'], settings.format,
                                     settings.zero_suppression)
                  if stmt['ydelta'] is not '' else None)
        c = cls(count, xdelta, ydelta, **kwargs)
        c.units = settings.units
        return c

    def __init__(self, count, xdelta=0.0, ydelta=0.0, **kwargs):
        super(RepeatHoleStmt, self).__init__(**kwargs)
        self.count = count
        self.xdelta = xdelta
        self.ydelta = ydelta

    def to_excellon(self, settings):
        stmt = 'R%d' % self.count
        if self.xdelta is not None and self.xdelta != 0.0:
            stmt += 'X%s' % write_gerber_value(self.xdelta, settings.format,
                                               settings.zero_suppression)
        if self.ydelta is not None and self.ydelta != 0.0:
            stmt += 'Y%s' % write_gerber_value(self.ydelta, settings.format,
                                               settings.zero_suppression)
        return stmt

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.xdelta is not None:
                self.xdelta = inch(self.xdelta)
            if self.ydelta is not None:
                self.ydelta = inch(self.ydelta)

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.xdelta is not None:
                self.xdelta = metric(self.xdelta)
            if self.ydelta is not None:
                self.ydelta = metric(self.ydelta)

    def __str__(self):
        return '<Repeat Hole: %d times, offset X: %g Y: %g>' % (
            self.count,
            self.xdelta if self.xdelta is not None else 0,
            self.ydelta if self.ydelta is not None else 0)


class CommentStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        return cls(line.lstrip(';'))

    def __init__(self, comment, **kwargs):
        super(CommentStmt, self).__init__(**kwargs)
        self.comment = comment

    def to_excellon(self, settings=None):
        return ';%s' % self.comment


class HeaderBeginStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(HeaderBeginStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'M48'


class HeaderEndStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(HeaderEndStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'M95'


class RewindStopStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(RewindStopStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return '%'


class ZAxisRoutPositionStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(ZAxisRoutPositionStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'M15'


class RetractWithClampingStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(RetractWithClampingStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'M16'


class RetractWithoutClampingStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(RetractWithoutClampingStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'M17'


class CutterCompensationOffStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(CutterCompensationOffStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G40'


class CutterCompensationLeftStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(CutterCompensationLeftStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G41'


class CutterCompensationRightStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(CutterCompensationRightStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G42'


class EndOfProgramStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, settings, **kwargs):
        match = re.compile(r'M30X?(?P<x>\d*\.?\d*)?Y?'
                           '(?P<y>\d*\.?\d*)?').match(line)
        stmt = match.groupdict()
        x = (parse_gerber_value(stmt['x'], settings.format,
                                settings.zero_suppression)
             if stmt['x'] is not '' else None)
        y = (parse_gerber_value(stmt['y'], settings.format,
                                settings.zero_suppression)
             if stmt['y'] is not '' else None)
        c = cls(x, y, **kwargs)
        c.units = settings.units
        return c

    def __init__(self, x=None, y=None, **kwargs):
        super(EndOfProgramStmt, self).__init__(**kwargs)
        self.x = x
        self.y = y

    def to_excellon(self, settings=None):
        stmt = 'M30'
        if self.x is not None:
            stmt += 'X%s' % write_gerber_value(self.x)
        if self.y is not None:
            stmt += 'Y%s' % write_gerber_value(self.y)
        return stmt

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.x is not None:
                self.x = inch(self.x)
            if self.y is not None:
                self.y = inch(self.y)

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.x is not None:
                self.x = metric(self.x)
            if self.y is not None:
                self.y = metric(self.y)

    def offset(self, x_offset=0, y_offset=0):
        if self.x is not None:
            self.x += x_offset
        if self.y is not None:
            self.y += y_offset


class UnitStmt(ExcellonStatement):

    @classmethod
    def from_settings(cls, settings):
        """Create the unit statement from the FileSettings"""

        return cls(settings.units, settings.zeros)

    @classmethod
    def from_excellon(cls, line, **kwargs):
        units = 'inch' if 'INCH' in line else 'metric'
        zeros = 'leading' if 'LZ' in line else 'trailing'
        if '0000.00' in line:
            format = (4, 2)
        elif '000.000' in line:
            format = (3, 3)
        elif '00.0000' in line:
            format = (2, 4)
        else:
            format = None
        return cls(units, zeros, format, **kwargs)

    def __init__(self, units='inch', zeros='leading', format=None, **kwargs):
        super(UnitStmt, self).__init__(**kwargs)
        self.units = units.lower()
        self.zeros = zeros
        self.format = format

    def to_excellon(self, settings=None):
        # TODO This won't export the invalid format statement if it exists
        stmt = '%s,%s' % ('INCH' if self.units == 'inch' else 'METRIC',
                          'LZ' if self.zeros == 'leading'
                          else 'TZ')
        return stmt

    def to_inch(self):
        self.units = 'inch'

    def to_metric(self):
        self.units = 'metric'


class IncrementalModeStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        return cls('off', **kwargs) if 'OFF' in line else cls('on', **kwargs)

    def __init__(self, mode='off', **kwargs):
        super(IncrementalModeStmt, self).__init__(**kwargs)
        if mode.lower() not in ['on', 'off']:
            raise ValueError('Mode may be "on" or "off"')
        self.mode = mode

    def to_excellon(self, settings=None):
        return 'ICI,%s' % ('OFF' if self.mode == 'off' else 'ON')


class VersionStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        version = int(line.split(',')[1])
        return cls(version, **kwargs)

    def __init__(self, version=1, **kwargs):
        super(VersionStmt, self).__init__(**kwargs)
        version = int(version)
        if version not in [1, 2]:
            raise ValueError('Valid versions are  1 or 2')
        self.version = version

    def to_excellon(self, settings=None):
        return 'VER,%d' % self.version


class FormatStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        fmt = int(line.split(',')[1])
        return cls(fmt, **kwargs)

    def __init__(self, format=1, **kwargs):
        super(FormatStmt, self).__init__(**kwargs)
        format = int(format)
        if format not in [1, 2]:
            raise ValueError('Valid formats are 1 or 2')
        self.format = format

    def to_excellon(self, settings=None):
        return 'FMAT,%d' % self.format

    @property
    def format_tuple(self):
        return (self.format, 6 - self.format)


class LinkToolStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        linked = [int(tool) for tool in line.split('/')]
        return cls(linked, **kwargs)

    def __init__(self, linked_tools, **kwargs):
        super(LinkToolStmt, self).__init__(**kwargs)
        self.linked_tools = [int(x) for x in linked_tools]

    def to_excellon(self, settings=None):
        return '/'.join([str(x) for x in self.linked_tools])


class MeasuringModeStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        if not ('M71' in line or 'M72' in line):
            raise ValueError('Not a measuring mode statement')
        return cls('inch', **kwargs) if 'M72' in line else cls('metric', **kwargs)

    def __init__(self, units='inch', **kwargs):
        super(MeasuringModeStmt, self).__init__(**kwargs)
        units = units.lower()
        if units not in ['inch', 'metric']:
            raise ValueError('units must be "inch" or "metric"')
        self.units = units

    def to_excellon(self, settings=None):
        return 'M72' if self.units == 'inch' else 'M71'

    def to_inch(self):
        self.units = 'inch'

    def to_metric(self):
        self.units = 'metric'


class RouteModeStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(RouteModeStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G00'


class LinearModeStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(LinearModeStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G01'


class DrillModeStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(DrillModeStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G05'


class AbsoluteModeStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(AbsoluteModeStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G90'


class UnknownStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, **kwargs):
        return cls(line, **kwargs)

    def __init__(self, stmt, **kwargs):
        super(UnknownStmt, self).__init__(**kwargs)
        self.stmt = stmt

    def to_excellon(self, settings=None):
        return self.stmt

    def __str__(self):
        return "<Unknown Statement: %s>" % self.stmt


class SlotStmt(ExcellonStatement):
    """
    G85 statement.  Defines a slot created by multiple drills between two specified points.

    Format is two coordinates, split by G85in the middle, for example, XnY0nG85XnYn
    """

    @classmethod
    def from_points(cls, start, end):

        return cls(start[0], start[1], end[0], end[1])

    @classmethod
    def from_excellon(cls, line, settings, **kwargs):
        # Split the line based on the G85 separator
        sub_coords = line.split('G85')
        (x_start_coord, y_start_coord) = SlotStmt.parse_sub_coords(sub_coords[0], settings)
        (x_end_coord, y_end_coord) = SlotStmt.parse_sub_coords(sub_coords[1], settings)

        # Some files seem to specify only one of the coordinates
        if x_end_coord == None:
            x_end_coord = x_start_coord
        if y_end_coord == None:
            y_end_coord = y_start_coord

        c = cls(x_start_coord, y_start_coord, x_end_coord, y_end_coord, **kwargs)
        c.units = settings.units
        return c

    @staticmethod
    def parse_sub_coords(line, settings):

        x_coord = None
        y_coord = None

        if line[0] == 'X':
            splitline = line.strip('X').split('Y')
            x_coord = parse_gerber_value(splitline[0], settings.format,
                                         settings.zero_suppression)
            if len(splitline) == 2:
                y_coord = parse_gerber_value(splitline[1], settings.format,
                                             settings.zero_suppression)
        else:
            y_coord = parse_gerber_value(line.strip(' Y'), settings.format,
                                         settings.zero_suppression)

        return (x_coord, y_coord)


    def __init__(self, x_start=None, y_start=None, x_end=None, y_end=None, **kwargs):
        super(SlotStmt, self).__init__(**kwargs)
        self.x_start = x_start
        self.y_start = y_start
        self.x_end = x_end
        self.y_end = y_end
        self.mode = None

    def to_excellon(self, settings):
        stmt = ''

        if self.x_start is not None:
            stmt += 'X%s' % write_gerber_value(self.x_start, settings.format,
                                               settings.zero_suppression)
        if self.y_start is not None:
            stmt += 'Y%s' % write_gerber_value(self.y_start, settings.format,
                                               settings.zero_suppression)

        stmt += 'G85'

        if self.x_end is not None:
            stmt += 'X%s' % write_gerber_value(self.x_end, settings.format,
                                               settings.zero_suppression)
        if self.y_end is not None:
            stmt += 'Y%s' % write_gerber_value(self.y_end, settings.format,
                                               settings.zero_suppression)

        return stmt

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.x_start is not None:
                self.x_start = inch(self.x_start)
            if self.y_start is not None:
                self.y_start = inch(self.y_start)
            if self.x_end is not None:
                self.x_end = inch(self.x_end)
            if self.y_end is not None:
                self.y_end = inch(self.y_end)

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.x_start is not None:
                self.x_start = metric(self.x_start)
            if self.y_start is not None:
                self.y_start = metric(self.y_start)
            if self.x_end is not None:
                self.x_end = metric(self.x_end)
            if self.y_end is not None:
                self.y_end = metric(self.y_end)

    def offset(self, x_offset=0, y_offset=0):
        if self.x_start is not None:
            self.x_start += x_offset
        if self.y_start is not None:
            self.y_start += y_offset
        if self.x_end is not None:
            self.x_end += x_offset
        if self.y_end is not None:
            self.y_end += y_offset

    def __str__(self):
        start_str = ''
        if self.x_start is not None:
            start_str += 'X: %g ' % self.x_start
        if self.y_start is not None:
            start_str += 'Y: %g ' % self.y_start

        end_str = ''
        if self.x_end is not None:
            end_str += 'X: %g ' % self.x_end
        if self.y_end is not None:
            end_str += 'Y: %g ' % self.y_end

        return '<Slot Statement: %s to %s>' % (start_str, end_str)

def pairwise(iterator):
    """ Iterate over list taking two elements at a time.

    e.g. [1, 2, 3, 4, 5, 6] ==> [(1, 2), (3, 4), (5, 6)]
    """
    a, b = itertools.tee(iterator)
    itr = zip(itertools.islice(a, 0, None, 2), itertools.islice(b, 1, None, 2))
    for elem in itr:
        yield elem
