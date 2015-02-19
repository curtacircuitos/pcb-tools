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

from .utils import (parse_gerber_value, write_gerber_value, decimal_string,
                    inch, metric)


__all__ = ['ExcellonTool', 'ToolSelectionStmt', 'CoordinateStmt',
           'CommentStmt', 'HeaderBeginStmt', 'HeaderEndStmt',
           'RewindStopStmt', 'EndOfProgramStmt', 'UnitStmt',
           'IncrementalModeStmt', 'VersionStmt', 'FormatStmt', 'LinkToolStmt',
           'MeasuringModeStmt', 'RouteModeStmt', 'DrillModeStmt',
           'AbsoluteModeStmt', 'RepeatHoleStmt', 'UnknownStmt',
           'ExcellonStatement',]


class ExcellonStatement(object):
    """ Excellon Statement abstract base class
    """
    @classmethod
    def from_excellon(cls, line):
        raise NotImplementedError('from_excellon must be implemented in a '
                                  'subclass')

    def to_excellon(self, settings=None):
        raise NotImplementedError('to_excellon must be implemented in a '
                                  'subclass')

    def to_inch(self):
        pass

    def to_metric(self):
        pass

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

    @classmethod
    def from_excellon(cls, line, settings):
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
        commands = re.split('([BCFHSTZ])', line)[1:]
        commands = [(command, value) for command, value in pairwise(commands)]
        args = {}
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
        self.settings = settings
        self.number = kwargs.get('number')
        self.feed_rate = kwargs.get('feed_rate')
        self.retract_rate = kwargs.get('retract_rate')
        self.rpm = kwargs.get('rpm')
        self.diameter = kwargs.get('diameter')
        self.max_hit_count = kwargs.get('max_hit_count')
        self.depth_offset = kwargs.get('depth_offset')
        self.hit_count = 0

    def to_excellon(self, settings=None):
        fmt = self.settings.format
        zs = self.settings.zero_suppression
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

    def __repr__(self):
        unit = 'in.' if self.settings.units == 'inch' else 'mm'
        fmtstr = '<ExcellonTool %%02d: %%%d.%dg%%s dia.>' % self.settings.format
        return fmtstr % (self.number, self.diameter, unit)


class ToolSelectionStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
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
        tool = int(line[:2])
        if len(line) > 2:
            compensation_index = int(line[2:])
        return cls(tool, compensation_index)

    def __init__(self, tool, compensation_index=None):
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


class CoordinateStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, settings):
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
        return cls(x_coord, y_coord)

    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

    def to_excellon(self, settings):
        stmt = ''
        if self.x is not None:
            stmt += 'X%s' % write_gerber_value(self.x, settings.format,
                                               settings.zero_suppression)
        if self.y is not None:
            stmt += 'Y%s' % write_gerber_value(self.y, settings.format,
                                               settings.zero_suppression)
        return stmt

    def to_inch(self):
        if self.x is not None:
            self.x = inch(self.x)
        if self.y is not None:
            self.y = inch(self.y)

    def to_metric(self):
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
    def from_excellon(cls, line, settings):
        match = re.compile(r'R(?P<rcount>[0-9]*)X?(?P<xdelta>\d*\.?\d*)?Y?'
                           '(?P<ydelta>\d*\.?\d*)?').match(line)
        stmt = match.groupdict()
        count = int(stmt['rcount'])
        xdelta = (parse_gerber_value(stmt['xdelta'], settings.format,
                                     settings.zero_suppression)
                  if stmt['xdelta']  is not '' else None)
        ydelta = (parse_gerber_value(stmt['ydelta'], settings.format,
                                     settings.zero_suppression)
                  if stmt['ydelta']  is not '' else None)
        return cls(count, xdelta, ydelta)

    def __init__(self, count, xdelta=0.0, ydelta=0.0):
        self.count = count
        self.xdelta = xdelta
        self.ydelta = ydelta

    def to_excellon(self, settings):
        stmt = 'R%d' % self.count
        if self.xdelta != 0.0:
            stmt += 'X%s' % write_gerber_value(self.xdelta, settings.format,
                                               settings.zero_suppression)
        if self.ydelta != 0.0:
            stmt += 'Y%s' % write_gerber_value(self.ydelta, settings.format,
                                               settings.zero_suppression)
        return stmt

    def to_inch(self):
        self.xdelta = inch(self.xdelta)
        self.ydelta = inch(self.ydelta)

    def to_metric(self):
        self.xdelta = metric(self.xdelta)
        self.ydelta = metric(self.ydelta)

    def __str__(self):
        return '<Repeat Hole: %d times>' % self.count


class CommentStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
        return cls(line.lstrip(';'))

    def __init__(self, comment):
        self.comment = comment

    def to_excellon(self, settings=None):
        return ';%s' % self.comment


class HeaderBeginStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self, settings=None):
        return 'M48'


class HeaderEndStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self, settings=None):
        return 'M95'


class RewindStopStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self, settings=None):
        return '%'


class EndOfProgramStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line, settings):
        match = re.compile(r'M30X?(?P<x>\d*\.?\d*)?Y?'
                           '(?P<y>\d*\.?\d*)?').match(line)
        stmt = match.groupdict()
        x = (parse_gerber_value(stmt['x'], settings.format,
                                settings.zero_suppression)
             if stmt['x'] is not '' else None)
        y = (parse_gerber_value(stmt['y'], settings.format,
                                settings.zero_suppression)
             if stmt['y'] is not '' else None)
        return cls(x, y)

    def __init__(self, x=None, y=None):
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
        if self.x is not None:
            self.x = inch(self.x)
        if self.y is not None:
            self.y = inch(self.y)

    def to_metric(self):
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
    def from_excellon(cls, line):
        units = 'inch' if 'INCH' in line else 'metric'
        zeros = 'leading' if 'LZ' in line else 'trailing'
        return cls(units, zeros)

    def __init__(self, units='inch', zeros='leading'):
        self.units = units.lower()
        self.zeros = zeros

    def to_excellon(self, settings=None):
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
    def from_excellon(cls, line):
        return cls('off') if 'OFF' in line else cls('on')

    def __init__(self, mode='off'):
        if mode.lower() not in ['on', 'off']:
            raise ValueError('Mode may be "on" or "off"')
        self.mode = mode

    def to_excellon(self, settings=None):
        return 'ICI,%s' % ('OFF' if self.mode == 'off' else 'ON')


class VersionStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
        version = int(line.split(',')[1])
        return cls(version)

    def __init__(self, version=1):
        version = int(version)
        if version not in [1, 2]:
            raise ValueError('Valid versions are  1 or 2')
        self.version = version

    def to_excellon(self, settings=None):
        return 'VER,%d' % self.version


class FormatStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
        fmt = int(line.split(',')[1])
        return cls(fmt)

    def __init__(self, format=1):
        format = int(format)
        if format not in [1, 2]:
            raise ValueError('Valid formats are 1 or 2')
        self.format = format

    def to_excellon(self, settings=None):
        return 'FMAT,%d' % self.format


class LinkToolStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
        linked = [int(tool) for tool in line.split('/')]
        return cls(linked)

    def __init__(self, linked_tools):
        self.linked_tools = [int(x) for x in linked_tools]

    def to_excellon(self, settings=None):
        return '/'.join([str(x) for x in self.linked_tools])


class MeasuringModeStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
        if not ('M71' in line or 'M72' in line):
            raise ValueError('Not a measuring mode statement')
        return cls('inch') if 'M72' in line else cls('metric')

    def __init__(self, units='inch'):
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

    def __init__(self):
        pass

    def to_excellon(self, settings=None):
        return 'G00'


class DrillModeStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self, settings=None):
        return 'G05'


class AbsoluteModeStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self, settings=None):
        return 'G90'


class UnknownStmt(ExcellonStatement):

    @classmethod
    def from_excellon(cls, line):
        return cls(line)

    def __init__(self, stmt):
        self.stmt = stmt

    def to_excellon(self, settings=None):
        return self.stmt

    def __str__(self):
        return "<Unknown Statement: %s>" % self.stmt


def pairwise(iterator):
    """ Iterate over list taking two elements at a time.

    e.g. [1, 2, 3, 4, 5, 6] ==> [(1, 2), (3, 4), (5, 6)]
    """
    itr = iter(iterator)
    while True:
        yield tuple([next(itr) for i in range(2)])
