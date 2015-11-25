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


class PathElement(object):
    def __init__(self, segments=None):
        if segments:
            self._segments = segments
        else:
            self._segments = []

    @property
    def start(self):
        return self._segments[0].start

    @property
    def end(self):
        return self._segments[-1].end

    @property
    def ends(self):
        return [self.start, self.end]

    @property
    def nodes(self):
        return [x.start for x in self._segments] + [self._segments[-1].end]

    @property
    def segments(self):
        return self._segments

    @property
    def aperture(self):
        return self._segments[0].aperture

    def add_segment(self, segment):
        if isinstance(Circle, segment.aperture) and \
                        segment.aperture.diameter != self.aperture.diameter:
            raise ValueError("Aperture is not circular or does not match")
        if segment.start in self.nodes and segment.end in self.nodes:
            raise ValueError("Segment would create a closed loop")
        if segment.start == self.end:
            self._segments.append(segment)
            return
        elif segment.end == self.start:
            self._segments = [segment] + self._segments
            return
        rsegment = segment.reversed
        if rsegment.start == self.start:
            self._segments = [rsegment] + self._segments
            return
        elif rsegment.end == self.end:
            self._segments.append(rsegment)
            return
        raise ValueError("Ends do not match")


class ElementOptimizer(object):
    def __init__(self):
        self._paths = []

    def add_element(self, line):
        existing_path = self.get_path_for_line(line)
        if existing_path:
            existing_path.add_segment(line)
        else:
            self.paths.append(PathElement([line]))

    @property
    def ends(self):
        return [x.start for x in self._paths] + [x.end for x in self._paths]

    @property
    def paths(self):
        return self._paths

    def get_path_for_line(self, line):
        for path in self._paths:
            pends = path.ends
            if line.start in pends or line.end in pends:
                if isinstance(Circle, line.aperture) and \
                        line.aperture.diameter != path.aperture.diameter:
                    return path
        return None

    def run(self):
        pass


class GerberFreecadContext(GerberContext):
    def __init__(self):
        super(GerberFreecadContext, self).__init__()
        self._sketch = None
        self._thin_draw = False
        self._verbose = False
        if self.units == 'inch':
            self.scale = (25.4, 25.4)
        self._pcb_ctx = None
        self._thickness = None
        self._elements = []
        self._deferred = []
        self._prefix = None
        self._base_body = None
        self._simplify_cad_elements = False

    @property
    def base_body(self):
        return self._base_body

    @base_body.setter
    def base_body(self, value):
        self._base_body = value

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
    def simplify_cad_elements(self):
        return self._simplify_cad_elements

    @simplify_cad_elements.setter
    def simplify_cad_elements(self, value):
        self._simplify_cad_elements = value

    @property
    def elements(self):
        return self._elements

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

    @staticmethod
    def _thin_draw_line(sketch, line):
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
                    " Found zero length line. Skipping line {0} {1}".format(
                        start, end
                    ))
            return
        if self._thin_draw:
            self._thin_draw_line(self._sketch, Line(start, end, None))
        else:
            if isinstance(line.aperture, Circle):
                if self._simplify_cad_elements:
                    self._deferred.append(line)
                    return
                element_name = self._prefix + str(len(self._elements) + 1)
                sketch_name = element_name + '_sketch'
                self.pcb_ctx.output_file.addObject(
                    'Sketcher::SketchObject', sketch_name
                )
                elem_sketch = getattr(self.pcb_ctx.output_file, sketch_name)
                elem_sketch.Support = self._sketch.Support

                self.pcb_ctx.output_file.recompute()
                width = line.aperture.diameter * self.scale_scalar
                lines, arcs = self._get_flanking_lines(start, end, width)
                for line in lines:
                    self._thin_draw_line(elem_sketch, line)
                for arc in arcs:
                    self._thin_draw_arc(elem_sketch, arc)

            elif isinstance(line.aperture, Rectangle):
                element_name = self._prefix + str(len(self._elements) + 1)
                sketch_name = element_name + '_sketch'
                self.pcb_ctx.output_file.addObject(
                    'Sketcher::SketchObject', sketch_name
                )
                elem_sketch = getattr(self.pcb_ctx.output_file, sketch_name)
                elem_sketch.Support = self._sketch.Support

                self.pcb_ctx.output_file.recompute()
                points = [tuple(map(mul, x, self.scale)) for x in line.vertices]
                for i in range(len(points)-1):
                    self._thin_draw_line(
                        elem_sketch, Line(points[i], points[i+1], None)
                    )
                self._thin_draw_line(
                    elem_sketch, Line(points[-1], points[0], None)
                )
            else:
                raise ValueError('Aperture type for line unrecognized : {0}'
                                 ''.format(line.aperture))

            self.pcb_ctx.output_file.recompute()
            self.pcb_ctx.output_file.addObject("PartDesign::Pad", element_name)
            element = getattr(self.pcb_ctx.output_file, element_name)
            element.Sketch = elem_sketch
            if self.thickness < 0:
                element.Reversed = True
            element.Length = abs(self.thickness)
            self._elements.append(element_name)
            if not self.pcb_ctx.nox:
                elem_sketch.ViewObject.hide()
            self.pcb_ctx.output_file.recompute()

    @staticmethod
    def _thin_draw_arc(sketch, arc):
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

    @staticmethod
    def _get_flanking_arcs(start, end, center, direction, width, radius=None):
        arcs = []

        x1 = start[0]
        y1 = start[1]
        x2 = end[0]
        y2 = end[1]
        xc = center[0]
        yc = center[1]

        if not radius:
            radius = sqrt((x1 - xc) ** 2 + (y1 - yc) ** 2)
        t = (width / 2.0) / radius

        x3 = x1 + (xc - x1) * t
        x4 = x1 - (xc - x1) * t
        y3 = y1 + (yc - y1) * t
        y4 = y1 - (yc - y1) * t

        x5 = x2 + (xc - x2) * t
        x6 = x2 - (xc - x2) * t
        y5 = y2 + (yc - y2) * t
        y6 = y2 - (yc - y2) * t

        if direction == 'clockwise':
            rdirection = 'counterclockwise'
        else:
            rdirection = 'clockwise'

        arcs.append(Arc((x3, y3), (x5, y5), center, direction, aperture=None))
        arcs.append(Arc((x4, y4), (x6, y6), center, direction, aperture=None))
        arcs.append(Arc((x3, y3), (x4, y4), start, direction, aperture=None))
        arcs.append(Arc((x5, y5), (x6, y6), start, rdirection, aperture=None))

        return arcs

    def _render_arc(self, arc, color):
        center = map(mul, arc.center, self.scale)
        start = map(mul, arc.start, self.scale)
        end = map(mul, arc.end, self.scale)
        if self._thin_draw:
            self._thin_draw_arc(self._sketch,
                                Arc(start, end, center, arc.direction, None)
                                )
            return
        else:
            if isinstance(arc.aperture, Circle):
                if self._simplify_cad_elements:
                    self._deferred.append(arc)
                    return
                element_name = self._prefix + str(len(self._elements) + 1)
                sketch_name = element_name + '_sketch'
                self.pcb_ctx.output_file.addObject(
                    'Sketcher::SketchObject', sketch_name
                )
                elem_sketch = getattr(self.pcb_ctx.output_file, sketch_name)
                elem_sketch.Support = self._sketch.Support

                self.pcb_ctx.output_file.recompute()

                width = arc.aperture.diameter * self.scale_scalar
                arcs = self._get_flanking_arcs(
                    start, end, center, arc.direction, width
                )
                for arc in arcs:
                    self._thin_draw_arc(elem_sketch, arc)

                self.pcb_ctx.output_file.recompute()
                self.pcb_ctx.output_file.addObject("PartDesign::Pad", element_name)
                element = getattr(self.pcb_ctx.output_file, element_name)
                element.Sketch = elem_sketch
                if self.thickness < 0:
                    element.Reversed = True
                element.Length = abs(self.thickness)
                self._elements.append(element_name)
                if not self.pcb_ctx.nox:
                    elem_sketch.ViewObject.hide()
                self.pcb_ctx.output_file.recompute()
                return
            else:
                raise ValueError('Aperture type for arc unrecognized : {0}'
                                 ''.format(arc.aperture))

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
                                " Found zero length line. "
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
            if self.thickness < 0:
                element.Reversed = True
            element.Length = abs(self.thickness)
            self._elements.append(element_name)
            if not self.pcb_ctx.nox:
                elem_sketch.ViewObject.hide()
            self.pcb_ctx.output_file.recompute()

    def _render_path(self, path):
        print(' render path {0} with {1} nodes'
              ''.format(path, len(path.segments)))

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
            if self.thickness < 0:
                element.Reversed = True
            element.Length = abs(self.thickness)
            self._elements.append(element_name)
            if not self.pcb_ctx.nox:
                elem_sketch.ViewObject.hide()
            self.pcb_ctx.output_file.recompute()

    def _render_rectangle(self, primitive, color):
        print(' unimplemented render_rectangle {0}'.format(primitive))

    def _render_obround(self, primitive, color):
        print(' unimplemented render_obround {0}'.format(primitive))

    def _render_polygon(self, primitive, color):
        print(' unimplemented render_polygon {0}'.format(primitive))

    def _render_drill(self, drill, color):
        center = map(mul, drill.position, self.scale)
        radius = (drill.diameter / 2) * self.scale_scalar

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
            if self.thickness < 0:
                element.Reversed = True
            element.Length = abs(self.thickness)
            self._elements.append(element_name)
            if not self.pcb_ctx.nox:
                elem_sketch.ViewObject.hide()
            self.pcb_ctx.output_file.recompute()

    def _render_test_record(self, primitive, color):
        print(' unimplemented render_test_record {0}'.format(primitive))

    def set_bounds(self, bounds):
        pass

    def _paint_background(self):
        pass

    def _paint_inverted_layer(self):
        pass

    def _optimize_deferred(self):
        optimizer = ElementOptimizer()
        for primitive in self._deferred:
            optimizer.add_element(primitive)
        optimizer.run()
        return optimizer

    def render_deferred(self):

        if not len(self._deferred):
            return

        print("Optimizing deferred elements")
        paths = self._optimize_deferred().paths

        print("Rendering Paths")
        try:
            from progress.bar import IncrementalBar
            _pbar = IncrementalBar(max=len(paths))
        except ImportError:
            _pbar = None

        for path in paths:
            self._render_path(path)
            if _pbar:
                _pbar.next()
        if _pbar:
            _pbar.finish()

    def fuse(self, name, simplify=True):
        print("Fusing {0} elements. This will take a while. "
              "Please be patient. ".format(name))
        self.pcb_ctx.output_file.addObject("Part::MultiFuse", name)
        fusion = getattr(self.pcb_ctx.output_file, name)
        elements = [
            getattr(self.pcb_ctx.output_file, x) for x in self._elements
            ]
        fusion.Shapes = elements
        self.pcb_ctx.output_file.recompute()
        if simplify or self.invert:
            self.pcb_ctx.output_file.addObject(
                'Part::Feature', name + '_fused'
            ).Shape = fusion.Shape.removeSplitter()
            if not self.pcb_ctx.nox:
                fusion.ViewObject.hide()
            self.pcb_ctx.output_file.recompute()

        if self.invert:
            cut_obj = self.pcb_ctx.output_file.addObject("Part::Cut", name + '_cut')
            cut_obj.Base = self._base_body
            if simplify:
                tool_obj = getattr(self.pcb_ctx.output_file, name + '_fused')
            else:
                tool_obj = fusion
            cut_obj.Tool = tool_obj
            self._base_body.ViewObject.hide()
            tool_obj.ViewObject.hide()
            self.pcb_ctx.output_file.recompute()


class PCBFreecadContext(PCBContext):
    def __init__(self, filenames, dialect, verbose):
        super(PCBFreecadContext, self).__init__(filenames, dialect, verbose)
        self._output_name = None
        self._output_file = None
        self._quick = False
        self._nox = False

        self._pcb_thickness = 1.6
        self._pcb_color = (171.0/255, 195.0/255, 84.0/255)

        self._outer_copper_thickness = 0.035
        self._copper_color = (205.0/255, 119.0/255, 55.0/255)

        self._mask_thickness = 0.005
        self._mask_color = (2.0/255, 55.0/255, 34.0/255)
        self._mask_alpha = 50

        self._silk_thickness = 0.005
        self._silk_color = (1.0, 1.0, 1.0)

        self._top_copper_obj = None
        self._bottom_copper_obj = None

    @property
    def nox(self):
        return self._nox

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

    @staticmethod
    def _get_top_face(solid):
        for idx, face in enumerate(solid.Shape.Faces):
            v = face.normalAt(0, 0)
            if (v.x, v.y, v.z) == (-0.0, -0.0, 1.0):
                return ['Face' + str(idx + 1)]
        raise Exception('Could not find top face!')

    @staticmethod
    def _get_bottom_face(solid):
        for idx, face in enumerate(solid.Shape.Faces):
            v = face.normalAt(0, 0)
            if (v.x, v.y, v.z) == (0.0, 0.0, -1.0):
                return ['Face' + str(idx + 1)]
        raise Exception('Could not find bottom face!')

    def _create_sketch_on_face(self, name, body, face):
        self._output_file.addObject('Sketcher::SketchObject', name)
        new_sketch = getattr(self._output_file, name)
        new_sketch.Support = (body, face)
        self._output_file.recompute()
        return new_sketch

    def _colorize_object(self, obj, color, alpha=0):
        if not self._nox:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.LineColor = color
            obj.ViewObject.PointColor = color
            obj.ViewObject.Transparency = alpha

    def _create_body(self):
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

        self._colorize_object(self._output_file.PCB_Body, self._pcb_color)
        if not self._nox:
            olsketch.ViewObject.hide()

    def _create_top_surface(self):
        self._create_top_copper()
        self._create_top_mask()
        # self._create_top_silk()
        self._create_top_paste()

    def _create_top_copper(self):
        print("Drawing top copper from {0}".format(self.layers.top))
        top_copper_sketch = self._create_sketch_on_face(
            'Top_Copper_Sketch',
            self._output_file.PCB_Body,
            self._get_top_face(self._output_file.PCB_Body)
        )
        ctx = GerberFreecadContext()
        ctx.sketch = top_copper_sketch
        ctx.thin_draw = False
        ctx.thickness = self._outer_copper_thickness
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'TCE_'
        ctx.simplify_cad_elements = False

        gerberfile = read(self.layers.top)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('Top_Copper')
        self._top_copper_obj = getattr(self._output_file, 'Top_Copper_fused')

        self._colorize_object(self._top_copper_obj, self._copper_color)
        self._output_file.recompute()

    def _create_top_mask(self):
        print("Drawing top mask from {0}".format(self.layers.topmask))
        top_mask_sketch = self._create_sketch_on_face(
            'Top_Mask_Sketch',
            self._output_file.PCB_Body,
            self._get_top_face(self._output_file.PCB_Body)
        )
        ctx = GerberFreecadContext()
        ctx.sketch = top_mask_sketch
        ctx.thin_draw = True
        ctx.verbose = self.verbose

        gerberfile = read(self.layers.outline)
        gerberfile.render(ctx, pbar=True)

        self._output_file.recompute()

        self._output_file.addObject("PartDesign::Pad", "Top_Mask_Body")
        self._output_file.Top_Mask_Body.Sketch = \
            self._output_file.Top_Mask_Sketch
        self._output_file.Top_Mask_Body.Length = \
            self._mask_thickness + self._outer_copper_thickness
        self._output_file.recompute()

        if not self._nox:
            top_mask_sketch.ViewObject.hide()

        ctx = GerberFreecadContext()
        ctx.sketch = top_mask_sketch
        ctx.thin_draw = False
        ctx.thickness = self._mask_thickness + self._outer_copper_thickness
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'TME_'
        ctx.invert = True
        ctx.base_body = self._output_file.Top_Mask_Body

        gerberfile = read(self.layers.topmask)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('Top_Mask')
        self._colorize_object(
            self._output_file.Top_Mask_cut,
            self._mask_color, self._mask_alpha
        )
        if not self.nox:
            self._output_file.Top_Mask_cut.ViewObject.Selectable = False
        self._output_file.recompute()

    def _create_top_silk(self):
        print("Drawing top silk from {0}".format(self.layers.topsilk))
        top_silk_sketch = self._create_sketch_on_face(
            'Top_Silk_Sketch',
            self._output_file.Top_Mask_cut,
            self._get_top_face(self._output_file.Top_Mask_cut)
        )
        ctx = GerberFreecadContext()
        ctx.sketch = top_silk_sketch
        ctx.thin_draw = False
        ctx.thickness = 2 * self._silk_thickness
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'TSE_'
        ctx.simplify_cad_elements = True

        gerberfile = read(self.layers.topsilk)
        gerberfile.render(ctx, pbar=True)

        if self._quick:
            for element in ctx.elements:
                obj = getattr(self._output_file, element)
                self._colorize_object(obj, self._silk_color)
        else:
            ctx.fuse('Top_Silk')
            obj = getattr(self._output_file, 'Top_Silk_fused')
            self._colorize_object(obj, self._silk_color)

        self._output_file.recompute()

    def _create_top_paste(self):
        pass

    def _create_bottom_surface(self):
        self._create_bottom_copper()
        self._create_bottom_mask()
        # self._create_bottom_silk()
        self._create_bottom_paste()

    def _create_bottom_copper(self):
        print("Drawing bottom copper from {0}".format(self.layers.bottom))
        bottom_copper_sketch = self._create_sketch_on_face(
            'Bottom_Copper_Sketch',
            self._output_file.PCB_Body,
            self._get_bottom_face(self._output_file.PCB_Body)
        )
        ctx = GerberFreecadContext()
        ctx.sketch = bottom_copper_sketch
        ctx.scale_y *= -1
        ctx.thin_draw = False
        ctx.thickness = self._outer_copper_thickness
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'BCE_'
        ctx.simplify_cad_elements = False

        gerberfile = read(self.layers.bottom)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('Bottom_Copper')
        self._bottom_copper_obj = getattr(self._output_file, 'Bottom_Copper_fused')

        self._colorize_object(self._bottom_copper_obj, self._copper_color)
        self._output_file.recompute()

    def _create_bottom_mask(self):
        print("Drawing bottom mask from {0}".format(self.layers.bottommask))
        bottom_mask_sketch = self._create_sketch_on_face(
            'Bottom_Mask_Sketch',
            self._output_file.PCB_Body,
            self._get_bottom_face(self._output_file.PCB_Body)
        )
        ctx = GerberFreecadContext()
        ctx.sketch = bottom_mask_sketch
        ctx.scale_y *= -1
        ctx.thin_draw = True
        ctx.verbose = self.verbose

        gerberfile = read(self.layers.outline)
        gerberfile.render(ctx, pbar=True)

        self._output_file.recompute()

        self._output_file.addObject("PartDesign::Pad", "Bottom_Mask_Body")
        self._output_file.Bottom_Mask_Body.Sketch = \
            self._output_file.Bottom_Mask_Sketch
        self._output_file.Bottom_Mask_Body.Length = \
            self._mask_thickness + self._outer_copper_thickness
        self._output_file.recompute()

        if not self._nox:
            bottom_mask_sketch.ViewObject.hide()

        ctx = GerberFreecadContext()
        ctx.sketch = bottom_mask_sketch
        ctx.thin_draw = False
        ctx.thickness = self._mask_thickness + self._outer_copper_thickness
        ctx.scale_y *= -1
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self
        ctx.prefix = 'BME_'
        ctx.invert = True
        ctx.base_body = self._output_file.Bottom_Mask_Body

        gerberfile = read(self.layers.bottommask)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('Bottom_Mask', simplify=False)
        self._colorize_object(
            self._output_file.Bottom_Mask_cut,
            self._mask_color, self._mask_alpha
        )
        if not self.nox:
            self._output_file.Bottom_Mask_cut.ViewObject.Selectable = False
        self._output_file.recompute()

    def _create_bottom_silk(self):
        pass

    def _create_bottom_paste(self):
        pass

    def _create_drills(self):
        print("Drawing drills from {0}".format(self.layers.drill))
        print("Drilling on Top Copper")
        drill_sketch_tc = self._create_sketch_on_face(
            'Drill_Sketch_TC',
            self._output_file.PCB_Body,
            self._get_top_face(self._output_file.PCB_Body)
        )

        ctx = GerberFreecadContext()
        ctx.sketch = drill_sketch_tc
        ctx.thin_draw = False
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self

        ctx.prefix = 'DRL_TC'
        ctx.thickness = self._outer_copper_thickness
        ctx.invert = True
        ctx.base_body = self._top_copper_obj

        gerberfile = read(self.layers.drill)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('Top_Copper_DRL', simplify=False)
        self._colorize_object(
            self._output_file.Top_Copper_DRL, self._copper_color
        )
        self._colorize_object(
            self._output_file.Top_Copper_DRL_cut, self._copper_color
        )
        self._output_file.recompute()

        print("Drilling on Bottom Copper")
        drill_sketch_bc = self._create_sketch_on_face(
            'Drill_Sketch_BC',
            self._output_file.PCB_Body,
            self._get_bottom_face(self._output_file.PCB_Body)
        )

        ctx = GerberFreecadContext()
        ctx.sketch = drill_sketch_bc
        ctx.scale_y *= -1
        ctx.thin_draw = False
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self

        ctx.prefix = 'DRL_BC'
        ctx.thickness = self._outer_copper_thickness
        ctx.invert = True
        ctx.base_body = self._bottom_copper_obj

        gerberfile = read(self.layers.drill)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('Bottom_Copper_DRL', simplify=False)
        self._colorize_object(
            self._output_file.Bottom_Copper_DRL, self._copper_color
        )
        self._colorize_object(
            self._output_file.Bottom_Copper_DRL_cut, self._copper_color
        )
        self._output_file.recompute()

        print("Drilling on PCB Body")
        drill_sketch_body = self._output_file.addObject(
            'Sketcher::SketchObject', 'Drill_Sketch_PCB'
        )

        ctx = GerberFreecadContext()
        ctx.sketch = drill_sketch_body
        ctx.thin_draw = False
        ctx.verbose = self.verbose
        ctx.pcb_ctx = self

        ctx.prefix = 'DRL_BODY'
        ctx.thickness = self._pcb_thickness
        ctx.invert = True
        ctx.base_body = self._output_file.PCB_Body

        gerberfile = read(self.layers.drill)
        gerberfile.render(ctx, pbar=True)

        ctx.fuse('PCB_Body_DRL', simplify=False)
        self._colorize_object(
            self._output_file.PCB_Body_DRL, self._pcb_color
        )
        self._colorize_object(
            self._output_file.PCB_Body_DRL_cut, self._pcb_color
        )
        self._output_file.recompute()

    def render(self, output_filename=None, quick=False, nox=False):
        self._quick = quick
        self._nox = nox
        if self.dialect:
            self.layers = self.dialect(self.filenames)
            if self.verbose:
                print("Using Layers : ")
                self.layers.print_layermap()
        else:
            raise AttributeError('FreeCAD backend needs a valid layer map to do '
                                 'anything. Specify an implemented layer name '
                                 'dialect and try again. ')

        if not self._nox:
            FreeCADGui.showMainWindow()

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

        if not self._nox:
            FreeCADGui.getMainWindow().close()
