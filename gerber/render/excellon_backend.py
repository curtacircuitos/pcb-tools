#! /usr/bin/env python
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

from .render import GerberContext
import math
import copy
import itertools

from ..primitives import *
from ..excellon_statements import *


class GerberExcellonContext(GerberContext):
    """GerberContext units are ignored in favor of passed gerberFile"""

    def __init__(self):
        GerberContext.__init__(self)
        self.drill_hits = {}
        self.verbose = False

    def set_bounds(self, bounds):
        pass

    # we lost all the info about compensation, depth offset, drill speed...
    def _render_drill(self, circle, color):

        # todo: optimize travels in a mid-step between _render_drill and self.statements
        if self.drill_hits.has_key(circle.diameter):
            self.drill_hits[circle.diameter].append(circle.position)
        else:
            self.drill_hits[circle.diameter] = [ circle.position, ]

    def statements(self,settings):
        import datetime
        yield CommentStmt(' pcb-tools generated on {0}'.format(datetime.datetime.now().isoformat()))
        yield RewindStopStmt()
        yield HeaderBeginStmt()
        yield MeasuringModeStmt(settings.units)
        
        for number,diameter in enumerate(self.drill_hits.keys(), start=1):
            yield ExcellonTool(settings, number=number, diameter=diameter)
        
        yield RewindStopStmt()

        for number,diameter in enumerate(self.drill_hits.keys(), start=1):
            yield ToolSelectionStmt(tool=number)
            for hit in self.drill_hits[diameter]:
                yield CoordinateStmt(*hit)

        yield EndOfProgramStmt()

    def dump(self,filename,settings):
        with open(filename, 'w') as f:
            for statement in self.statements(settings):
                f.write(statement.to_excellon(settings))
                f.write("\n")

