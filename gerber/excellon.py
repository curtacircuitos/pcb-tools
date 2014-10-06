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
    def __init__(self, statements, tools, hits, settings, filename=None):
        super(ExcellonFile, self).__init__(statements, settings, filename)
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

    def write(self, filename):
        with open(filename, 'w') as f:
            for statement in self.statements:
                f.write(statement.to_excellon() + '\n')
                

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
        return ExcellonFile(self.statements, self.tools, self.hits, self._settings(), filename)

    def dump(self, filename):
        if self.ctx is not None:
            self.ctx.dump(filename)

    def _parse(self, line):
        zs = self._settings()['zero_suppression']
        fmt = self._settings()['format']
        
        if line[0] == ';':
            self.statements.append(CommentStmt.from_excellon(line))
    
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

        elif line[:3] == 'G00':
            self.state = 'ROUT'

        elif line[:3] == 'G05':
            self.state = 'DRILL'
        
        elif ('INCH' in line or 'METRIC' in line) and ('LZ' in line or 'TZ' in line):
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

        # tool definition
        elif line[0] == 'T' and self.state == 'HEADER':
            tool = ExcellonTool.from_excellon(line, self._settings())
            self.tools[tool.number] = tool
            self.statements.append(tool)

        elif line[0] == 'T' and self.state != 'HEADER':
            stmt = ToolSelectionStmt.from_excellon(line)
            self.active_tool = self.tools[stmt.tool]
            #self.active_tool = self.tools[int(line.strip().split('T')[1])]
            self.statements.append(stmt)
            
        elif line[0] in ['X', 'Y']:
            stmt = CoordinateStmt.from_excellon(line, fmt, zs)
            x = stmt.x
            y = stmt.y
            self.statements.append(stmt)
            #x = None
            #y = None
            #if line[0] == 'X':
            #    splitline = line.strip('X').split('Y')
            #    x = parse_gerber_value(splitline[0].strip(), fmt, zs)
            #    if len(splitline) == 2:
            #        y = parse_gerber_value(splitline[1].strip(), fmt, zs)
            #else:
            #    y = parse_gerber_value(line.strip(' Y'), fmt, zs)
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
        
        else:
            self.statements.append(UnknownStmt.from_excellon(line))

    def _settings(self):
        return FileSettings(units=self.units, format=self.format,
                            zero_suppression=self.zero_suppression,
                            notation=self.notation)
        

if __name__ == '__main__':
    p = ExcellonParser()
    parsed = p.parse('examples/ncdrill.txt')
