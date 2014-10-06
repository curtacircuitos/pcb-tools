#! /usr/bin/env python
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
Excellon module
============
**Excellon file classes**

This module provides Excellon file classes and parsing utilities
"""
import re
from .excellon_statements import *
from .utils import parse_gerber_value
from .cnc import CncFile, FileSettings


def read(filename):
    """ Read data from filename and return an ExcellonFile
    """
    return ExcellonParser().parse(filename)


class ExcellonFile(CncFile):
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
    def __init__(self, tools, hits, settings, filename=None):
        super(ExcellonFile, self).__init__(settings, filename)
        self.tools = tools
        self.hits = hits

    def report(self):
        """ Print drill report
        """
        pass

    def render(self, filename, ctx):
        """ Generate image of file
        """
        for tool, pos in self.hits:
            ctx.drill(pos[0], pos[1], tool.diameter)
        ctx.dump(filename)


class ExcellonParser(object):
    """ Excellon File Parser
    """
    def __init__(self, ctx=None):
        self.ctx = ctx
        self.notation = 'absolute'
        self.units = 'inch'
        self.zero_suppression = 'trailing'
        self.format = (2, 5)
        self.state = 'INIT'
        self.statements = []
        self.tools = {}
        self.hits = []
        self.active_tool = None
        self.pos = [0., 0.]
        if ctx is not None:
            self.ctx.set_coord_format(zero_suppression='trailing',
                                      format=(2, 5), notation='absolute')

    def parse(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                self._parse(line)
        return ExcellonFile(self.tools, self.hits, self._settings(), filename)

    def dump(self, filename):
        if self.ctx is not None:
            self.ctx.dump(filename)

    def _parse(self, line):
        if 'M48' in line:
            self.statements.append(HeaderBeginStmt())
            self.state = 'HEADER'

        elif line[0] == '%':
            self.statements.append(RewindStopStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'

        elif 'M95' in line:
            self.statements.append(HeaderEndStmt())
            if self.state == 'HEADER':
                self.state = 'DRILL'

        elif 'G00' in line:
            self.state = 'ROUT'

        elif 'G05' in line:
            self.state = 'DRILL'

        if 'INCH' in line or line.strip() == 'M72':
            self.units = 'inch'

        elif 'METRIC' in line or line.strip() == 'M71':
            self.units = 'metric'

        if 'LZ' in line:
            self.zeros = 'L'

        elif 'TZ' in line:
            self.zeros = 'T'

        if 'ICI' in line and 'ON' in line or line.strip() == 'G91':
            self.notation = 'incremental'

        if 'ICI' in line and 'OFF' in line or line.strip() == 'G90':
            self.notation = 'incremental'

        zs = self._settings()['zero_suppression']
        fmt = self._settings()['format']

        # tool definition
        if line[0] == 'T' and self.state == 'HEADER':
            tool = ExcellonTool.from_line(line, self._settings())
            self.tools[tool.number] = tool

        elif line[0] == 'T' and self.state != 'HEADER':
            self.active_tool = self.tools[int(line.strip().split('T')[1])]

        if line[0] in ['X', 'Y']:
            x = None
            y = None
            if line[0] == 'X':
                splitline = line.strip('X').split('Y')
                x = parse_gerber_value(splitline[0].strip(), fmt, zs)
                if len(splitline) == 2:
                    y = parse_gerber_value(splitline[1].strip(), fmt, zs)
            else:
                y = parse_gerber_value(line.strip(' Y'), fmt, zs)
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
                self.hits.append((self.active_tool, self.pos))
                self.active_tool._hit()
                if self.ctx is not None:
                    self.ctx.drill(self.pos[0], self.pos[1],
                                   self.active_tool.diameter)

    def _settings(self):
        return FileSettings(units=self.units, format=self.format,
                            zero_suppression=self.zero_suppression,
                            notation=self.notation)


def pairwise(iterator):
    """ Iterate over list taking two elements at a time.

    e.g. [1, 2, 3, 4, 5, 6] ==> [(1, 2), (3, 4), (5, 6)]
    """
    itr = iter(iterator)
    while True:
        yield tuple([itr.next() for i in range(2)])
        

if __name__ == '__main__':
    p = parser()
    p.parse('examples/ncdrill.txt')
