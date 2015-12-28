#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Garret Fick <garret@ficksworkshop.com>

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
Excellon Tool Definition File module
====================
**Excellon file classes**

This module provides Excellon file classes and parsing utilities
"""

import re
try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO
    
from .excellon_statements import ExcellonTool
    
def loads(data, settings=None):
    """ Read tool file information and return a map of tools
    Parameters
    ----------
    data : string
        string containing Excellon Tool Definition file contents

    Returns
    -------
    dict tool name: ExcellonTool

    """
    return ExcellonToolDefinitionParser(settings).parse_raw(data)

class ExcellonToolDefinitionParser(object):
    """ Excellon File Parser

    Parameters
    ----------
    None
    """
    
    allegro_tool = re.compile(r'(?P<size>[0-9/.]+)\s+(?P<plated>P|N)\s+T(?P<toolid>[0-9]{2})\s+(?P<xtol>[0-9/.]+)\s+(?P<ytol>[0-9/.]+)')
    allegro_comment_mils = re.compile('Holesize (?P<toolid>[0-9]{1,2})\. = (?P<size>[0-9/.]+) Tolerance = \+(?P<xtol>[0-9/.]+)/-(?P<ytol>[0-9/.]+) (?P<plated>(PLATED)|(NON_PLATED)) MILS Quantity = [0-9]+')
    allegro_comment_mm = re.compile('Holesize (?P<toolid>[0-9]{1,2})\. = (?P<size>[0-9/.]+) Tolerance = \+(?P<xtol>[0-9/.]+)/-(?P<ytol>[0-9/.]+) (?P<plated>(PLATED)|(NON_PLATED)) MM Quantity = [0-9]+')
    
    matchers = [
                (allegro_tool, 'mils'),
                (allegro_comment_mils, 'mils'),
                (allegro_comment_mm, 'mm'),
                ]
    
    def __init__(self, settings=None):
        self.tools = {}
        self.settings = settings
        
    def parse_raw(self, data):
        for line in StringIO(data):
            self._parse(line.strip())
            
        return self.tools
            
    def _parse(self, line):
        
        for matcher in ExcellonToolDefinitionParser.matchers:
            m = matcher[0].match(line)
            if m:
                unit = matcher[1]
                
                size = float(m.group('size'))
                plated = m.group('plated')
                toolid = int(m.group('toolid'))
                xtol = float(m.group('xtol'))
                ytol = float(m.group('ytol'))
                
                size = self._convert_length(size, unit)
                xtol = self._convert_length(xtol, unit)
                ytol = self._convert_length(ytol, unit)
                
                tool = ExcellonTool(None, number=toolid, diameter=size)
                
                self.tools[tool.number] = tool
                
                break
                
    def _convert_length(self, value, unit):
        
        # Convert the value to mm
        if unit == 'mils':
            value /= 39.3700787402
            
        # Now convert to the settings unit
        if self.settings.units == 'inch':
            return value / 25.4
        else:
            # Already in mm
            return value
            