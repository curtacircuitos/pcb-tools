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


import re
from itertools import tee, izip
from .utils import parse_gerber_value
    



class Tool(object):

    @classmethod
    def from_line(cls, line, settings):
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
        
    def __init__(self, settings, **kwargs):
        self.number = kwargs.get('number')
        self.feed_rate = kwargs.get('feed_rate')
        self.retract_rate = kwargs.get('retract_rate')
        self.rpm = kwargs.get('rpm')
        self.diameter = kwargs.get('diameter')
        self.max_hit_count = kwargs.get('max_hit_count')
        self.depth_offset = kwargs.get('depth_offset')
        self.units = settings.get('units', 'inch')
        
    def __repr__(self):
        unit = 'in.' if self.units == 'inch' else 'mm'
        return '<Tool %d: %0.3f%s dia.>' % (self.number, self.diameter, unit)
        


class ExcellonParser(object):
    def __init__(self, ctx=None):
        self.ctx=ctx
        self.notation = 'absolute'
        self.units = 'inch'
        self.zero_suppression = 'trailing'
        self.format = (2,5)
        self.state = 'INIT'
        self.tools = {}
        self.hits = []
        self.active_tool = None
        self.pos = [0., 0.]
        if ctx is not None:
            zeros = 'L' if self.zero_suppression == 'leading' else 'T'
            x = self.format
            y = self.format
            self.ctx.set_coord_format(zeros, x, y)
    def parse(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                self._parse(line)
    
    def dump(self, filename='teste.svg'):
        if self.ctx is not None:
            self.ctx.dump(filename)
        
    def _parse(self, line):
        if 'M48' in line:
            self.state = 'HEADER'
        
        if 'G00' in line:
            self.state = 'ROUT'
        
        if 'G05' in line:
            self.state = 'DRILL'
        
        elif line[0] == '%' and self.state == 'HEADER':
            self.state = 'DRILL'
        
        if 'INCH' in line or line.strip() == 'M72':
            self.units = 'inch'
            
        elif 'METRIC' in line or line.strip() == 'M71':
            self.units = 'metric'
            
        if 'LZ' in line:
            self.zero_suppression = 'trailing'
            
        elif 'TZ' in line:
            self.zero_suppression = 'leading'

        if 'ICI' in line and 'ON' in line or line.strip() == 'G91':
            self.notation = 'incremental'
            
        if 'ICI' in line and 'OFF' in line or line.strip() == 'G90':
            self.notation = 'absolute'
        
        zs = self._settings()['zero_suppression']
        fmt = self._settings()['format']
        
        # tool definition
        if line[0] == 'T' and self.state == 'HEADER':
            tool = Tool.from_line(line,self._settings())
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
                    y = parse_gerber_value(splitline[1].strip(), fmt,zs)
            else:
                y = parse_gerber_value(line.strip(' Y'), fmt,zs)
            
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
                if self.ctx is not None:
                    self.ctx.drill(self.pos[0], self.pos[1],
                                   self.active_tool.diameter)
            
    def _settings(self):
        return {'units':self.units, 'zero_suppression':self.zero_suppression,
                'format': self.format}
        
def pairwise(iterator):
    itr = iter(iterator)
    while True:
        yield tuple([itr.next() for i in range(2)])
        
if __name__ == '__main__':
    from .render_svg import GerberSvgContext
    tools = []
    p = ExcellonParser(GerberSvgContext())
    p.parse('examples/ncdrill.txt')
    p.dump('excellon.svg')
            
            