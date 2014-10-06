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

from .utils import write_gerber_value


__all__ = ['ExcellonTool', 'CommentStmt', 'HeaderBeginStmt', 'HeaderEndStmt',
           ]


class ExcellonStatement(object):
    """ Excellon Statement abstract base class
    """
    def to_excellon(self):
        pass


class ExcellonTool(ExcellonStatement):
    """ Excellon Tool class

    Parameters
    ----------
    settings : FileSettings (dict-like)
        File-wide settings.

    kwargs : dict-like
        Tool settings from the excellon statement. Valid keys are:
            diameter : Tool diameter [expressed in file units]
            rpm : Tool RPM
            feed_rate : Z-axis tool feed rate
            retract_rate : Z-axis tool retraction rate
            max_hit_count : Number of hits allowed before a tool change
            depth_offset : Offset of tool depth from tip of tool.

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
    def from_line(cls, line, settings):
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
        format = settings['format']
        zero_suppression = settings['zero_suppression']
        for cmd, val in commands:
            if cmd == 'B':
                args['retract_rate'] = parse_gerber_value(val, format, zero_suppression)
            elif cmd == 'C':
                args['diameter'] = parse_gerber_value(val, format, zero_suppression)
            elif cmd == 'F':
                args['feed_rate'] = parse_gerber_value(val, format, zero_suppression)
            elif cmd == 'H':
                args['max_hit_count'] = parse_gerber_value(val, format, zero_suppression)
            elif cmd == 'S':
                args['rpm'] = 1000 * parse_gerber_value(val, format, zero_suppression)
            elif cmd == 'T':
                args['number'] = int(val)
            elif cmd == 'Z':
                args['depth_offset'] = parse_gerber_value(val, format, zero_suppression)
        return cls(settings, **args)

    def from_dict(cls, settings, tool_dict):
        return cls(settings, tool_dict)

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

    def to_excellon(self):
        fmt = self.settings['format']
        zs = self.settings['zero_suppression']
        stmt = 'T%d' % self.number
        if self.retract_rate:
            stmt += 'B%s' % write_gerber_value(self.retract_rate, fmt, zs)
        if self.diameter:
            stmt += 'C%s' % write_gerber_value(self.diameter, fmt, zs)
        if self.feed_rate:
            stmt += 'F%s' % write_gerber_value(self.feed_rate, fmt, zs)
        if self.max_hit_count:
            stmt += 'H%s' % write_gerber_value(self.max_hit_count, fmt, zs)
        if self.rpm:
            if self.rpm < 100000.:
                stmt += 'S%s' % write_gerber_value(self.rpm / 1000., fmt, zs)
            else:
                stmt += 'S%g' % self.rpm / 1000.
        if self.depth_offset:
            stmt += 'Z%s' % write_gerber_value(self.depth_offset, fmt, zs)
        return stmt

    def _hit(self):
        self.hit_count += 1

    def __repr__(self):
        unit = 'in.' if self.settings.units == 'inch' else 'mm'
        return '<ExcellonTool %d: %0.3f%s dia.>' % (self.number, self.diameter, unit)


class CommentStmt(ExcellonStatement):
    def __init__(self, comment):
        self.comment = comment

    def to_excellon(self):
        return ';%s' % comment


class HeaderBeginStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self):
        return 'M48'


class HeaderEndStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self):
        return 'M95'


class RewindStopStmt(ExcellonStatement):

    def __init__(self):
        pass

    def to_excellon(self):
        return '%'


class EndOfProgramStmt(ExcellonStatement):

    def __init__(self, x=None, y=None):
        self.x = x
        self.y = y

    def to_excellon(self):
        stmt = 'M30'
        if self.x is not None:
            stmt += 'X%s' % write_gerber_value(self.x)
        if self.y is not None:
            stmt += 'Y%s' % write_gerber_value(self.y)


class UnitStmt(ExcellonStatement):

    def __init__(self, units='inch', zero_suppression='trailing'):
        self.units = units.lower()
        self.zero_suppression = zero_suppression

    def to_excellon(self):
        stmt = '%s,%s' % ('INCH' if self.units == 'inch' else 'METRIC',
                          'LZ' if self.zero_suppression == 'trailing' else 'TZ')


class IncrementalModeStmt(ExcellonStatement):

    def __init__(self, mode='off'):
        if mode.lower() not in ['on', 'off']:
            raise ValueError('Mode may be "on" or "off")
        self.mode = 'off'

    def to_excellon(self):
        return 'ICI,%s' % 'OFF' if self.mode == 'off' else 'ON'


class VersionStmt(ExcellonStatement):

    def __init__(self, version=1):
        self.version = int(version)

    def to_excellon(self):
        return 'VER,%d' % self.version


class FormatStmt(ExcellonStatement):
    def __init__(self, format=1):
        self.format = int(format)

    def to_excellon(self):
        return 'FMAT,%d' % self.format


class LinkToolStmt(ExcellonStatement):

    def __init__(self, linked_tools):
        self.linked_tools = [int(x) for x in linked_tools]

    def to_excellon(self):
        return '/'.join([str(x) for x in self.linked_tools])


class MeasuringModeStmt(ExcellonStatement):
    
    def __init__(self, units='inch'):
        units = units.lower()
        if units not in ['inch', 'metric']:
            raise ValueError('units must be "inch" or "metric"')
        self.units = units
        
    def to_excellon(self):
        return 'M72' if self.units == 'inch' else 'M71'


