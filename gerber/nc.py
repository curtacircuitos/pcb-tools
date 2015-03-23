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
NC File module
====================
**NC (PADS-alike) file classes**

This module provides NC file classes and parsing utilities
"""

import math

from .excellon_statements import *
from .cam import CamFile, FileSettings
from .primitives import Drill
from .utils import inch, metric
from .excellon import ExcellonFile


def read(filename, settings=None):
    """ Read data from filename and return an ExcellonFile
    Parameters
        ----------
    filename : string
        Filename of file to parse

    settings : gerber.cam.FileSettings
        NC Files does not include enough information on its format 
        so it have to be provided

    Returns
    -------
    file : :class:`gerber.excellon.ExcellonFile`
        An ExcellonFile created from the specified file.

    """

    return ExcellonParser(settings).parse(filename)


class NcParser(object):
    """ NC File Parser

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
        with open(filename, 'r') as f:
            for line in f:
                self._parse(line.strip())
        return ExcellonFile(self.statements, self.tools, self.hits,
                            self._settings(), filename)

    def _parse(self, line):
        # skip empty lines
        if not line.strip():
            return

        if line[0] == '%':
            self.statements.append(RewindStopStmt())
        elif line[:3] == 'M30':
            stmt = EndOfProgramStmt.from_excellon(line, self._settings())
            self.statements.append(stmt)

        elif line[0] == 'T':
            tool = ExcellonTool.from_excellon(line, self._settings())
            self.tools[tool.number] = tool
            self.statements.append(tool)
            stmt = ToolSelectionStmt.from_excellon("T%02d" % tool.number)
            self.active_tool = tool
            self.statements.append(stmt)

        elif line[0] in ['X', 'Y']:
            stmt = CoordinateStmt.from_excellon(line, self._settings())
            x = stmt.x
            y = stmt.y
            self.statements.append(stmt)
            self.hits.append((self.active_tool, (x,y)))
            self.active_tool._hit()
        else:
            self.statements.append(UnknownStmt.from_excellon(line))

    def _settings(self):
        return FileSettings(units=self.units, format=self.format,
                            zeros=self.zeros, notation=self.notation)


def detect_nc_format(filename):
    """ Detect NC file format.

    Parameters
    ----------
    filename : string
        Name of the file to parse. This does only check if the file is actually
        an NC file.

    Returns
    -------
        True or False
        Unfortunately, NC files does not include settings information.
    """
    with open(filename) as f:
        lines = f.readlines()
        # suppose there is at least one tool
        return lines[0][0] == '%' and lines[1][0] == 'T' and lines[-1].strip() == 'M30'
