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

from ..primitives import *
from ..gerber_statements import *

## this was initially a method of primitives
## it has been moved here because it is gerber_backend specific
def aperture_data(aperture):

    if isinstance(aperture, Circle) or isinstance(aperture, Drill):
        return ('C', aperture.diameter)  # what about %ADD10C,0.5X0.25*% and %ADD10C,0.5X0.29X0.29*% ??

    elif isinstance(aperture, Rectangle):
        return ('R', aperture.width, aperture.height)  # what about %ADD10C,0.5X0.25*% and %ADD10C,0.5X0.29X0.29*% ??

    elif isinstance(aperture, Obround):
        return ('O', aperture.width, aperture.height)  # what about %ADD10C,0.5X0.25*% and %ADD10C,0.5X0.29X0.29*% ??

    elif isinstance(aperture, Polygon):
        raise TypeError('Polygon aperture are not supported yet')

    elif isinstance(aperture, type(None)):
        raise TypeError('Likely a macro built that didn\'t work')

    else:
        raise TypeError('Unknown aperture type')


class GerberRs274xContext(GerberContext):
    """GerberContext units are ignored in favor of passed gerberFile"""

    def __init__(self):
        GerberContext.__init__(self)
        self.primitives_statements = []
        self.apertures_dcode = {}
        self.apertures_data = []
        self.macros = {}
        self.x = None
        self.y = None
        self.op = None
        self.aperture = None
        self.interpolation = None
        self.direction = None
        # note: Image polarity is deprecated
        self.level_polarity = None    # standard default is 'dark', but at the same time, standard says it is wise to not rely on it
        #self.rounding_error = (10**self.settings.format[1])/2
        self.verbose = False

    def set_bounds(self, bounds):
        pass


    def _render_level_polarity(self,level_polarity):
        if self.level_polarity != level_polarity:
            self.primitives_statements.append(LPParamStmt('LP',level_polarity))
            self.level_polarity = level_polarity


    def _render_aperture(self,aperture):

        data = aperture_data(aperture)
        if data != self.aperture:

            if not self.apertures_dcode.has_key(data):
                dcode = 10+len(self.apertures_data)
                self.apertures_dcode[data] = dcode
                self.apertures_data.append(data)
            else:
                dcode = self.apertures_dcode[data]

            self.primitives_statements.append(ApertureStmt(dcode))
            self.aperture = data


    def _render_coord(self,(x,y),interpolation,direction,op,(i,j)=(None,None)):

        if x is not None and self.x is not None and x == self.x: #and math.fabs(x-self.x) < self.rounding_error:
            x = None
        else:
            self.x = x

        if y is not None and self.y is not None and y == self.y: #and math.fabs(y-self.y) < self.rounding_error:
            y = None
        else:
            self.y = y

        (function, ) = {
            ( None,     None,               'linear', None)              : ( 'G01',  ),
            ( None,     None,               'arc',    'clockwise')       : ( 'G02', ),
            ( None,     None,               'arc',    'counterclockwise'): ( 'G03', ),
            ( 'linear', None,               'linear', None)              : ( None,  ),
            ( 'linear', None,               'arc',    'clockwise')       : ( 'G02', ),
            ( 'linear', None,               'arc',    'counterclockwise'): ( 'G03', ),
            ( 'arc',    'clockwise',        'linear', None)              : ( 'G01',  ),
            ( 'arc',    'clockwise',        'arc',    'clockwise')       : ( None, ),
            ( 'arc',    'clockwise',        'arc',    'counterclockwise'): ( 'G03', ),
            ( 'arc',    'counterclockwise', 'linear', None)              : ( 'G01',  ),
            ( 'arc',    'counterclockwise', 'arc',    'clockwise')       : ( 'G02', ),
            ( 'arc',    'counterclockwise', 'arc',    'counterclockwise'): ( None, ),
        }[(self.interpolation, self.direction, interpolation, direction)]


        assert(op is not None)
        if op == "D01" and self.op == "D01":
                op=None
        else:
            self.op = op

        if op != 'D02' or x is not None or y is not None:
            self.interpolation = interpolation
            self.direction = direction
            if op == 'D01' and x is None and y is None:
                x = self.x
            self.primitives_statements.append(CoordStmt(function=function, x=x, y=y, i=i, j=j, op=op, settings=None))


    def declare_primitive(self,primitive):
        if self.verbose:
            self.primitives_statements.append(CoordStmt(function=None, x=None, y=None, i=None, j=None, op=None, settings=None))
            self.primitives_statements.append(CommentStmt(" " + str(primitive)))

    def comment(self,info):
        if self.verbose:
            if info == '':
                self.primitives_statements.append(CoordStmt(function=None, x=None, y=None, i=None, j=None, op=None, settings=None))
            else:
                self.primitives_statements.append(CommentStmt(' ' + info))

    def _render_line(self, line, color):
        self.comment('')
        self.comment('Line  %s' % ( line.level_polarity ))
        self.comment(' from %s' % ( line.start, ))
        self.comment('   to %s' % ( line.end, ))
        self._render_level_polarity(line.level_polarity)
        self._render_aperture(line.aperture)
        if line.start != line.end:
            self._render_coord(line.start, 'linear', None, 'D02')
            self._render_coord(line.end, 'linear', None, 'D01')
        else:
            self._render_coord(line.end, 'linear', None, 'D03')


    def _render_arc(self, arc, color):
        self.comment('')
        self.comment('Arc   %s' % ( arc.level_polarity ))
        self.comment(' from %s' % ( arc.start, ))
        self.comment('   to %s' % ( arc.end, ))
        self.comment('  ctr %s' % ( arc.center, ))
        self._render_level_polarity(arc.level_polarity)
        self._render_aperture(arc.aperture)
        self._render_coord(arc.start, 'linear', None, 'D02')
        center = (arc.center[0] - arc.start[0], arc.center[1]-arc.start[1])
        self._render_coord(arc.end, 'arc', arc.direction, 'D01', center)


    def _render_region(self, region, color):
        ## arcs in region are not supported yet :-(
        assert(len(region.points) > 0)
        self.comment('')
        self.comment('Region %s' % ( arc.level_polarity ))
        self._render_level_polarity(region.level_polarity)
        self._render_coord(region.points[0], 'linear', None, 'D02')
        for point in region.points[1:]:
            self._render_coord(point, 'linear', None, 'D01')


    def _render_circle(self, circle, color):
        self.comment('')
        self.comment('Circle %s' % ( circle.level_polarity ))
        self.comment('   pos %s' % ( circle.position, ))
        self.comment('   rad %s' % ( circle.radius, ))
        self.declare_primitive(circle)
        self._render_level_polarity(circle.level_polarity)
        self._render_aperture(circle)
        self._render_coord(circle.position, 'linear', None, 'D03')


    def _render_rectangle(self, rectangle, color):
        self.comment('')
        self.comment('  Rect %s' % ( rectangle.level_polarity ))
        self.comment('   pos %s' % ( rectangle.position, ))
        self.comment('   wdt %s' % ( rectangle.width ))
        self.comment('   hgt %s' % ( rectangle.height ))
        self._render_level_polarity(rectangle.level_polarity)
        self._render_aperture(rectangle)
        self._render_coord(rectangle.position, 'linear', None, 'D03')

    def _render_obround(self, obround, color):
        self.comment('')
        self.comment('Obround %s' % ( obround.level_polarity ))
        self.comment('    pos %s' % ( obround.position, ))
        self.comment('    wdt %s' % ( obround.width ))
        self.comment('    hgt %s' % ( obround.height ))
        self._render_level_polarity(obround.level_polarity)
        self._render_aperture(obround)
        self._render_coord(obround.position, 'linear', None, 'D03')

    def _render_drill(self, circle, color):
        self.comment('')
        self.comment('Drill %s' % ( circle.level_polarity ))
        self.comment('  pos %s' % ( circle.position, ))
        self.comment('  rad %s' % ( circle.radius ))
        self._render_level_polarity(circle.level_polarity)
        self._render_aperture(circle)
        self._render_coord(circle.position, 'linear', None, 'D03')

    def _render_test_record(self, primitive, color):
        self.comment('')
        self.comment('Test record')
        self.comment('   position %s' % (primitive.position,))
        self.comment('   net      %s' % (primitive.net_name,))
        self.comment('   layer    %s' % (primitive.layer,))

    def aperture_debug_statements(self,dcode,atype,fmod):
        if self.verbose:
            yield CoordStmt(function=None, x=None, y=None, i=None, j=None, op=None, settings=None)
            if atype == 'C' and len(fmod) == 1:
                yield CommentStmt(' Circle Aperture of radius %.4g on DCODE D%d' % (fmod[0], dcode))
            elif atype == 'R' and len(fmod) == 2:
                yield CommentStmt(' Rectangle Aperture of size <%.4g,%.4g> on DCODE D%d' % (fmod[0], fmod[1], dcode))
            elif atype == 'O' and len(fmod) == 2:
                yield CommentStmt(' Obround Aperture of size <%.4g,%.4g> on DCODE D%d' % (fmod[0], fmod[1], dcode))
            else:
                raise TypeError('unsupported aperture type')


    def statements(self,settings):
        import datetime
        yield CommentStmt(' pcb-tools generated on {0}'.format(datetime.datetime.now().isoformat()))
        yield MOParamStmt("MO", settings.units)
        yield FSParamStmt('FS', 
                    zero_suppression=settings.zero_suppression,
                    notation=settings.notation, 
                    format=settings.format)
        ## macro are to be exploded in rs274x.py so they become primitives
        ## otherewise, they should be listed here

        for aperture in self.apertures_data:
            dcode = self.apertures_dcode[aperture]
            atype = aperture[0]
            fmod = aperture[1:]
            smod = "X".join(["%.4g" % x for x in fmod])
            for stmt in self.aperture_debug_statements(dcode,atype,fmod):
                yield stmt
            yield ADParamStmt('AD', dcode, atype, smod)


        #yield LPParamStmt('LP', 'dark')
        yield QuadrantModeStmt('multi-quadrant')

        for statement in self.primitives_statements:
            yield statement

        yield QuadrantModeStmt('single-quadrant')
        yield CoordStmt(function=None, x=0, y=0, i=None, j=None, op="D02", settings=None)
        yield EofStmt()

    def dump(self,filename,settings):
        with open(filename, 'w') as f:
            for statement in self.statements(settings):
                f.write(statement.to_gerber(settings))
                f.write("\n")

