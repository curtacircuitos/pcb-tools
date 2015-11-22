#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Chintalagiri Shashank <shashank@chintal.in>

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
Docstring for freecad_backend
"""

import os
import platform
import sys
from math import sqrt
from operator import mul

from .render import GerberContext
from .render import PCBContext

from gerber.common import read
from ..primitives import *

try:
    import FreeCAD
    import FreeCADGui
    import Part
except ImportError:
    if 'FREECADPATH' in os.environ.keys():
        FREECADPATH = os.environ['FREECADPATH']
    else:
        if platform.system() == 'Windows':
            FREECADPATH = '/c/apps/FreeCAD/bin'
        else:
            FREECADPATH = '/usr/lib/freecad/lib'
    sys.path.append(FREECADPATH)
    import FreeCAD
    import FreeCADGui
    import Part


class GerberFreecadContext(GerberContext):
    def __init__(self):
        super(GerberFreecadContext, self).__init__()
        self._sketch = None
        self._thin_draw = False
        self._invert_x = False
        self._invert_y = False
        self._verbose = False
        if self.units == 'inch':
            self.scale = (25.4, 25.4)
        self._pcb_ctx = None
        self._thickness = None
        self._elements = []
        self._prefix = None

    @property
    def sketch(self):
        return self._sketch

    @sketch.setter
    def sketch(self, value):
        self._sketch = value

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, value):
        self._prefix = value

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, value):
        self._thickness = value

    @property
    def pcb_ctx(self):
        return self._pcb_ctx

    @pcb_ctx.setter
    def pcb_ctx(self, value):
        self._pcb_ctx = value

    @property
    def thin_draw(self):
        return self._thin_draw

    @thin_draw.setter
    def thin_draw(self, value):
        self._thin_draw = value

    @property
    def invert_x(self):
        return self._invert_x

    @invert_x.setter
    def invert_x(self, value):
        self._invert_x = value

    @property
    def invert_y(self):
        return self._invert_y

    @invert_y.setter
    def invert_y(self, value):
        self._invert_y = value

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = value

    @staticmethod
    def _get_flanking_lines(start, end, width):
        lines = []
        arcs = []

        x1 = start[0]
        y1 = start[1]
        x2 = end[0]
        y2 = end[1]

        dx = x1 - x2
        dy = y1 - y2
        dist = sqrt(dx * dx + dy * dy)
        dx /= dist
        dy /= dist

        x3 = x1 + (width/2) * dy
        y3 = y1 - (width/2) * dx
        x4 = x2 - (width/2) * dy
        y4 = y2 + (width/2) * dx

        x5 = x1 - (width/2) * dy
        y5 = y1 + (width/2) * dx
        x6 = x2 + (width/2) * dy
        y6 = y2 - (width/2) * dx

        lines.append(Line((x3, y3), (x6, y6), None))
        lines.append(Line((x5, y5), (x4, y4), None))

        arcs.append(Arc((x3, y3), (x5, y5), (x1, y1), 'counterclockwise', None))
        arcs.append(Arc((x4, y4), (x6, y6), (x2, y2), 'counterclockwise', None))

        return lines, arcs

    def _thin_draw_line(self, sketch, line):
        start = line.start
        end = line.end
        sketch.addGeometry(
            Part.Line(
                FreeCAD.Vector(start[0], start[1], 0),
                FreeCAD.Vector(end[0], end[1], 0)
            )
        )

    def _render_line(self, line, color):
        start = map(mul, line.start, self.scale)
        end = map(mul, line.end, self.scale)
        if start == end:
            if self.verbose:
                print(
                    "Found zero length line. Skipping line {0} {1}".format(
                        start, end
                    ))
            return
        if self._thin_draw:
            self._thin_draw_line(self._sketch, Line(start, end, None))
        else:
            element_name = self._prefix + str(len(self._elements) + 1)
            sketch_name = element_name + '_sketch'
            self.pcb_ctx.output_file.addObject(
                'Sketcher::SketchObject', sketch_name
            )
            elem_sketch = getattr(self.pcb_ctx.output_file, sketch_name)
            elem_sketch.Support = self._sketch.Support

            self.pcb_ctx.output_file.recompute()
            if isinstance(line.aperture, Circle):
                width = line.aperture.diameter * self.scale_scalar
                lines, arcs = self._get_flanking_lines(start, end, width)
                for line in lines:
                    self._thin_draw_line(elem_sketch, line)
                for arc in arcs:
                    self._thin_draw_arc(elem_sketch, arc)

            elif isinstance(line.aperture, Rectangle):
                points = [tuple(map(mul, x, self.scale)) for x in line.vertices]
                for i in range(len(points)-1):
                    self._thin_draw_line(
                        elem_sketch, Line(points[i], points[i+1], None)
                    )
                self._thin_draw_line(
                    elem_sketch, Line(points[-1], points[0], None)
                )

            self.pcb_ctx.output_file.recompute()
            self.pcb_ctx.output_file.addObject("PartDesign::Pad", element_name)
            element = getattr(self.pcb_ctx.output_file, element_name)
            element.Sketch = elem_sketch
            element.Length = self.thickness
            self._elements.append(element_name)
            self.pcb_ctx.output_file.recompute()

    def _thin_draw_arc(self, sketch, arc):
        if arc.direction == 'clockwise':
            start_angle = arc.end_angle
            end_angle = arc.start_angle
        else:
            start_angle = arc.start_angle
            end_angle = arc.end_angle
        center = arc.center
        radius = arc.radius
        sketch.addGeometry(
                Part.ArcOfCircle(
                    Part.Circle(
                        FreeCAD.Vector(center[0], center[1], 0),
                        FreeCAD.Vector(0, 0, 1), radius
                    ),
                    start_angle,
                    end_angle
                )
            )

    def _render_arc(self, arc, color):
        center = map(mul, arc.center, self.scale)
        start = map(mul, arc.start, self.scale)
        end = map(mul, arc.end, self.scale)
        if self._thin_draw:
            self._thin_draw_arc(self._sketch,
                                Arc(start, end, center, arc.direction, None)
                                )
        else:
            print 'unimplemented render_arc', arc

    def _render_region(self, region, color):
        if self._thin_draw:
            for primitive in region.primitives:
                if isinstance(primitive, Line):
                    self._render_line(primitive, None)
                elif isinstance(primitive, Arc):
                    self._render_arc(primitive, None)
        else:
            element_name = self._prefix + str(len(self._elements) + 1)
            sketch_name = element_name + '_sketch'
            self.pcb_ctx.output_file.addObject(
                'Sketcher::SketchObject', sketch_name
            )
            elem_sketch = getattr(self.pcb_ctx.output_file, sketch_name)
            elem_sketch.Support = self._sketch.Support

            self.pcb_ctx.output_file.recompute()
            for primitive in region.primitives:
                if isinstance(primitive, Line):
                    start = map(mul, primitive.start, self.scale)
                    end = map(mul, primitive.end, self.scale)
                    if start == end:
                        if self.verbose:
                            print(
                                "Found zero length line. "
                                "Skipping line {0} {1}".format(
                                    start, end
                                ))
                        continue
                    self._thin_draw_line(elem_sketch, Line(start, end, None))
                if isinstance(primitive, Arc):
                    center = map(mul, primitive.center, self.scale)
                    start = map(mul, primitive.start, self.scale)
                    end = map(mul, primitive.end, self.scale)
                    self._thin_draw_arc(
                        elem_sketch,
                        Arc(start, end, center, primitive.direction, None)
                    )
            self.pcb_ctx.output_file.recompute()

            self.pcb_ctx.output_file.addObject("PartDesign::Pad", element_name)
            element = getattr(self.pcb_ctx.output_file, element_name)
            element.Sketch = elem_sketch
            element.Length = self.thickness
            self._elements.append(element_name)
            self.pcb_ctx.output_file.recompute()

    def _render_circle(self, circle, color):
        center = map(mul, circle.position, self.scale)
        radius = circle.radius * self.scale_scalar

        if self.thin_draw:
            self._sketch.addGeometry(
                    Part.Circle(
                        FreeCAD.Vector(center[0], center[1], 0),
                        FreeCAD.Vector(0, 0, 1), radius
                    ),
                )
        else:
            element_name = self._prefix + str(len(self._elements) + 1)
            sketch_name = element_name + '_sketch'
            self.pcb_ctx.output_file.addObject(
                'Sketcher::SketchObject', sketch_name
            )
            elem_sketch = getattr(self.pcb_ctx.output_file, sketch_name)
            elem_sketch.Support = self._sketch.Support

            self.pcb_ctx.output_file.recompute()
            elem_sketch.addGeometry(
                    Part.Circle(
                        FreeCAD.Vector(center[0], center[1], 0),
                        FreeCAD.Vector(0, 0, 1), radius
                    ),
                )
            self.pcb_ctx.output_file.recompute()
            self.pcb_ctx.output_file.addObject("PartDesign::Pad", element_name)
            element = getattr(self.pcb_ctx.output_file, element_name)
            element.Sketch = elem_sketch
            element.Length = self.thickness
            self._elements.append(element_name)
            self.pcb_ctx.output_file.recompute()

    def _render_rectangle(self, primitive, color):
        print 'render_rectangle', primitive

    def _render_obround(self, primitive, color):
        print 'render_obround', primitive

    def _render_polygon(self, primitive, color):
        print 'render_polygon', primitive

    def _render_drill(self, primitive, color):
        print 'render_drill', primitive

    def _render_test_record(self, primitive, color):
        print 'render_test_record', primitive

    def set_bounds(self, bounds):
        pass

    def _paint_background(self):
        pass

    def fuse(self, name):
        print("Fusing {0} elements. This will take a while. Please be patient. "
              "Maybe get yourself a cup of coffee.".format(name))
        self.pcb_ctx.output_file.addObject("Part::MultiFuse", name)
        fusion = getattr(self.pcb_ctx.output_file, name)
        elements = [
            getattr(self.pcb_ctx.output_file, x) for x in self._elements
            ]
        fusion.Shapes = elements
        self.pcb_ctx.output_file.recompute()
        self.pcb_ctx.output_file.addObject(
            'Part::Feature', name + '_fused'
        ).Shape = fusion.Shape.removeSplitter()
        self.pcb_ctx.output_file.recompute()


class PCBFreecadContext(PCBContext):
    def __init__(self, filenames, dialect, verbose):
        super(PCBFreecadContext, self).__init__(filenames, dialect, verbose)
        self._output_name = None
        self._output_file = None
        self._pcb_thickness = 1.6
        self._outer_copper_thickness = 0.035
        self._quick = False

    @property
    def output_file(self):
        return self._output_file

    def _create_output_file(self):
        try:
            os.remove(self._output_name + '.fcstd')
        except OSError:
            pass
        self._output_file = FreeCAD.newDocument(self._output_name)

    def _write_output_file(self):
        self._output_file.saveAs(self._output_name + '.fcstd')

    def _get_top_face(self):
        # TODO Figure out how to get this
        return ['Face15']

    def _get_bottom_face(self):
        # TODO Figure out how to get this
        return ['Face14']

    def _create_sketch_on_face(self, name, body, face):
        self._output_file.addObject('Sketcher::SketchObject', name)
        new_sketch = getattr(self._output_file, name)
        new_sketch.Support = (body, face)
        self._output_file.recompute()
        return new_sketch

    def _create_body(self):
        if self.verbose:
            print("Thin drawing outline from {0}".format(self.layers.outline))
        olsketch = self._output_file.addObject(
            "Sketcher::SketchObject", "Outline Sketch"
        )
        ctx = GerberFreecadContext()
        ctx.sketch = olsketch
        ctx.thin_draw = True
        ctx.verbose = self.verbose

        gerberfile = read(self.layers.outline)
        gerberfile.render(ctx)

        self._output_file.recompute()

        self._output_file.addObject("PartDesign::Pad", "PCB_Body")
        self._output_file.PCB_Body.Sketch = self._output_file.Outline_Sketch
        self._output_file.PCB_Body.Length = self._pcb_thickness
        self._output_file.recompute()

    def _create_top_surface(self):
        self._create_top_copper()
        self._create_top_mask()
        self._create_top_silk()
        self._create_top_paste()

    def _create_top_copper(self):
        top_copper_sketch = self._create_sketch_on_face(
            'Top_Copper_Sketch', self._output_file.PCB_Body, self._get_top_face()
        )
        ctx = GerberFreecadContext()
        ctx.sketch = top_copper_sketch
        ctx.thin_draw = False
        ctx.thickness = self._outer_copper_thickness
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'TCE_'

        gerberfile = read(self.layers.top)
        gerberfile.render(ctx)

        if not self._quick:
            ctx.fuse('Top_Copper')

        self._output_file.recompute()

    def _create_top_mask(self):
        pass

    def _create_top_silk(self):
        pass

    def _create_top_paste(self):
        pass

    def _create_bottom_surface(self):
        self._create_bottom_copper()
        self._create_bottom_mask()
        self._create_bottom_silk()
        self._create_bottom_paste()

    def _create_bottom_copper(self):
        bottom_copper_sketch = self._create_sketch_on_face(
            'Bottom_Copper_Sketch', self._output_file.PCB_Body, self._get_bottom_face()
        )
        ctx = GerberFreecadContext()
        ctx.sketch = bottom_copper_sketch
        ctx.scale_y *= -1
        ctx.thin_draw = False
        ctx.thickness = self._outer_copper_thickness
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'BCE_'

        gerberfile = read(self.layers.bottom)
        gerberfile.render(ctx)

        if not self._quick:
            ctx.fuse('Bottom_Copper')

        self._output_file.recompute()

    def _create_bottom_mask(self):
        pass

    def _create_bottom_silk(self):
        pass

    def _create_bottom_paste(self):
        pass

    def _create_drills(self):
        pass

    def render(self, output_filename=None, quick=False):
        self._quick = quick
        if self.dialect:
            self.layers = self.dialect(self.filenames)
            if self.verbose:
                print("Using Layers : ")
                self.layers.print_layermap()
        else:
            raise AttributeError('FreeCAD backend needs a valid layer map to do '
                                 'anything. Specify an implemented layer name '
                                 'dialect and try again. ')
        if not output_filename:
            output_filename = self.layers.pcbname
        if os.path.splitext(output_filename)[1].upper() == 'FCSTD':
            output_filename = output_filename[:-len('.fcstd')]
        self._output_name = output_filename

        self._create_output_file()

        self._create_body()
        self._create_top_surface()
        self._create_bottom_surface()
        self._create_drills()

        self._write_output_file()
