#!/usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2015 Hamilton Kibbe <ham@hamiltonkib.be> and Paulo Henrique Silva
# <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from math import asin
import math

from .primitives import *
from .utils import validate_coordinates, inch, metric, rotate_point



# TODO: Add support for aperture macro variables
__all__ = ['AMPrimitive', 'AMCommentPrimitive', 'AMCirclePrimitive',
           'AMVectorLinePrimitive', 'AMOutlinePrimitive', 'AMPolygonPrimitive',
           'AMMoirePrimitive', 'AMThermalPrimitive', 'AMCenterLinePrimitive',
           'AMLowerLeftLinePrimitive', 'AMUnsupportPrimitive']


class AMPrimitive(object):
    """ Aperture Macro Primitive Base Class

    Parameters
    ----------
    code : int
        primitive shape code

    exposure : str
        on or off Primitives with exposure on create a slid part of
        the macro aperture, and primitives with exposure off erase the
        solid part created previously in the aperture macro definition.
        .. note::
            The erasing effect is limited to the aperture definition in
            which it occurs.

    Returns
    -------
    primitive : :class: `gerber.am_statements.AMPrimitive`

    Raises
    ------
    TypeError, ValueError
    """

    def __init__(self, code, exposure=None):
        VALID_CODES = (0, 1, 2, 4, 5, 6, 7, 20, 21, 22, 9999)
        if not isinstance(code, int):
            raise TypeError('Aperture Macro Primitive code must be an integer')
        elif code not in VALID_CODES:
            raise ValueError('Invalid Code. Valid codes are %s.' %
                             ', '.join(map(str, VALID_CODES)))
        if exposure is not None and exposure.lower() not in ('on', 'off'):
            raise ValueError('Exposure must be either on or off')
        self.code = code
        self.exposure = exposure.lower() if exposure is not None else None

    def to_inch(self):
        raise NotImplementedError('Subclass must implement `to-inch`')

    def to_metric(self):
        raise NotImplementedError('Subclass must implement `to-metric`')

    @property
    def _level_polarity(self):
        if self.exposure == 'off':
            return 'clear'
        return 'dark'

    def to_primitive(self, units):
        """ Return a Primitive instance based on the specified macro params.
        """
        print('Rendering {}s is not supported yet.'.format(str(self.__class__)))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class AMCommentPrimitive(AMPrimitive):
    """ Aperture Macro Comment primitive. Code 0

    The comment primitive has no image meaning. It is used to include human-
    readable comments into the AM command.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.1:** Comment, primitive code 0

    Parameters
    ----------
    code : int
        Aperture Macro primitive code. 0 Indicates an AMCommentPrimitive

    comment : str
        The comment as a string.

    Returns
    -------
    CommentPrimitive : :class:`gerber.am_statements.AMCommentPrimitive`
        An Initialized AMCommentPrimitive

    Raises
    ------
    ValueError
    """
    @classmethod
    def from_gerber(cls, primitive):
        primitive = primitive.strip()
        code = int(primitive[0])
        comment = primitive[1:]
        return cls(code, comment)

    def __init__(self, code, comment):
        if code != 0:
            raise ValueError('Not a valid Aperture Macro Comment statement')
        super(AMCommentPrimitive, self).__init__(code)
        self.comment = comment.strip(' *')

    def to_inch(self):
        pass

    def to_metric(self):
        pass

    def to_gerber(self, settings=None):
        return '0 %s *' % self.comment

    def to_primitive(self, units):
        """
        Returns None - has not primitive representation
        """
        return None

    def __str__(self):
        return '<Aperture Macro Comment: %s>' % self.comment


class AMCirclePrimitive(AMPrimitive):
    """ Aperture macro Circle primitive. Code 1

    A circle primitive is defined by its center point and diameter.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.2:** Circle, primitive code 1

    Parameters
    ----------
    code : int
        Circle Primitive code. Must be 1

    exposure : string
        'on' or 'off'

    diameter : float
        Circle diameter

    position : tuple (<float>, <float>)
        Position of the circle relative to the macro origin

    Returns
    -------
    CirclePrimitive : :class:`gerber.am_statements.AMCirclePrimitive`
        An initialized AMCirclePrimitive

    Raises
    ------
    ValueError, TypeError
    """
    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(',')
        code = int(modifiers[0])
        exposure = 'on' if float(modifiers[1]) == 1 else 'off'
        diameter = float(modifiers[2])
        position = (float(modifiers[3]), float(modifiers[4]))
        return cls(code, exposure, diameter, position)

    @classmethod
    def from_primitive(cls, primitive):
        return cls(1, 'on', primitive.diameter, primitive.position)

    def __init__(self, code, exposure, diameter, position):
        validate_coordinates(position)
        if code != 1:
            raise ValueError('CirclePrimitive code is 1')
        super(AMCirclePrimitive, self).__init__(code, exposure)
        self.diameter = diameter
        self.position = position

    def to_inch(self):
        self.diameter = inch(self.diameter)
        self.position = tuple([inch(x) for x in self.position])

    def to_metric(self):
        self.diameter = metric(self.diameter)
        self.position = tuple([metric(x) for x in self.position])

    def to_gerber(self, settings=None):
        data = dict(code=self.code,
                    exposure='1' if self.exposure == 'on' else 0,
                    diameter=self.diameter,
                    x=self.position[0],
                    y=self.position[1])
        return '{code},{exposure},{diameter},{x},{y}*'.format(**data)

    def to_primitive(self, units):
        return Circle((self.position), self.diameter, units=units, level_polarity=self._level_polarity)


class AMVectorLinePrimitive(AMPrimitive):
    """ Aperture Macro Vector Line primitive. Code 2 or 20.

    A vector line is a rectangle defined by its line width, start, and end
    points. The line ends are rectangular.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.3:** Vector Line, primitive code 2 or 20.

    Parameters
    ----------
    code : int
        Vector Line Primitive code. Must be either 2 or 20.

    exposure : string
        'on' or 'off'

    width : float
        Line width

    start : tuple (<float>, <float>)
        coordinate of line start point

    end : tuple (<float>, <float>)
        coordinate of line end point

    rotation : float
        Line rotation about the origin.

    Returns
    -------
    LinePrimitive : :class:`gerber.am_statements.AMVectorLinePrimitive`
        An initialized AMVectorLinePrimitive

    Raises
    ------
    ValueError, TypeError
    """

    @classmethod
    def from_primitive(cls, primitive):
        return cls(2, 'on', primitive.aperture.width, primitive.start, primitive.end, 0)

    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(',')
        code = int(modifiers[0])
        exposure = 'on' if float(modifiers[1]) == 1 else 'off'
        width = float(modifiers[2])
        start = (float(modifiers[3]), float(modifiers[4]))
        end = (float(modifiers[5]), float(modifiers[6]))
        rotation = float(modifiers[7])
        return cls(code, exposure, width, start, end, rotation)

    def __init__(self, code, exposure, width, start, end, rotation):
        validate_coordinates(start)
        validate_coordinates(end)
        if code not in (2, 20):
            raise ValueError('VectorLinePrimitive codes are 2 or 20')
        super(AMVectorLinePrimitive, self).__init__(code, exposure)
        self.width = width
        self.start = start
        self.end = end
        self.rotation = rotation

    def to_inch(self):
        self.width = inch(self.width)
        self.start = tuple([inch(x) for x in self.start])
        self.end = tuple([inch(x) for x in self.end])

    def to_metric(self):
        self.width = metric(self.width)
        self.start = tuple([metric(x) for x in self.start])
        self.end = tuple([metric(x) for x in self.end])

    def to_gerber(self, settings=None):
        fmtstr = '{code},{exp},{width},{startx},{starty},{endx},{endy},{rotation}*'
        data = dict(code=self.code,
                    exp=1 if self.exposure == 'on' else 0,
                    width=self.width,
                    startx=self.start[0],
                    starty=self.start[1],
                    endx=self.end[0],
                    endy=self.end[1],
                    rotation=self.rotation)
        return fmtstr.format(**data)

    def to_primitive(self, units):
        """
        Convert this to a primitive. We use the Outline to represent this (instead of Line)
        because the behaviour of the end caps is different for aperture macros compared to Lines
        when rotated.
        """

        # Use a line to generate our vertices easily
        line = Line(self.start, self.end, Rectangle(None, self.width, self.width))
        vertices = line.vertices

        aperture = Circle((0, 0), 0)

        lines = []
        prev_point = rotate_point(vertices[-1], self.rotation, (0, 0))
        for point in vertices:
            cur_point = rotate_point(point, self.rotation, (0, 0))

            lines.append(Line(prev_point, cur_point, aperture))

        return Outline(lines, units=units, level_polarity=self._level_polarity)


class AMOutlinePrimitive(AMPrimitive):
    """ Aperture Macro Outline primitive. Code 4.

    An outline primitive is an area enclosed by an n-point polygon defined by
    its start point and n subsequent points. The outline must be closed, i.e.
    the last point must be equal to the start point. Self intersecting
    outlines are not allowed.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.6:** Outline, primitive code 4.

     Parameters
    ----------
    code : int
        OutlinePrimitive code. Must be 6.

    exposure : string
        'on' or 'off'

    start_point : tuple (<float>, <float>)
        coordinate of outline start point

    points : list of tuples (<float>, <float>)
        coordinates of subsequent points

    rotation : float
        outline rotation about the origin.

    Returns
    -------
    OutlinePrimitive : :class:`gerber.am_statements.AMOutlineinePrimitive`
        An initialized AMOutlinePrimitive

    Raises
    ------
    ValueError, TypeError
    """

    @classmethod
    def from_primitive(cls, primitive):

        start_point = (round(primitive.primitives[0].start[0], 6), round(primitive.primitives[0].start[1], 6))
        points = []
        for prim in primitive.primitives:
            points.append((round(prim.end[0], 6), round(prim.end[1], 6)))

        rotation = 0.0

        return cls(4, 'on', start_point, points, rotation)

    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")

        code = int(modifiers[0])
        exposure = "on" if float(modifiers[1]) == 1 else "off"
        n = int(float(modifiers[2]))
        start_point = (float(modifiers[3]), float(modifiers[4]))
        points = []
        for i in range(n):
            points.append((float(modifiers[5 + i * 2]),
                           float(modifiers[5 + i * 2 + 1])))
        rotation = float(modifiers[-1])
        return cls(code, exposure, start_point, points, rotation)

    def __init__(self, code, exposure, start_point, points, rotation):
        """ Initialize AMOutlinePrimitive
        """
        validate_coordinates(start_point)
        for point in points:
            validate_coordinates(point)
        if code != 4:
            raise ValueError('OutlinePrimitive code is 4')
        super(AMOutlinePrimitive, self).__init__(code, exposure)
        self.start_point = start_point
        if points[-1] != start_point:
            raise ValueError('OutlinePrimitive must be closed')
        self.points = points
        self.rotation = rotation

    def to_inch(self):
        self.start_point = tuple([inch(x) for x in self.start_point])
        self.points = tuple([(inch(x), inch(y)) for x, y in self.points])

    def to_metric(self):
        self.start_point = tuple([metric(x) for x in self.start_point])
        self.points = tuple([(metric(x), metric(y)) for x, y in self.points])

    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            exposure="1" if self.exposure == "on" else "0",
            n_points=len(self.points),
            start_point="%.6g,%.6g" % self.start_point,
            points=",\n".join(["%.6g,%.6g" % point for point in self.points]),
            rotation=str(self.rotation)
        )
        return "{code},{exposure},{n_points},{start_point},{points},{rotation}*".format(**data)

    def to_primitive(self, units):
        """
        Convert this to a drawable primitive. This uses the Outline instead of Line
        primitive to handle differences in end caps when rotated.
        """

        lines = []
        prev_point = rotate_point(self.start_point, self.rotation)
        for point in self.points:
            cur_point = rotate_point(point, self.rotation)

            lines.append(Line(prev_point, cur_point, Circle((0,0), 0)))

            prev_point = cur_point

        if lines[0].start != lines[-1].end:
            raise ValueError('Outline must be closed')

        return Outline(lines, units=units, level_polarity=self._level_polarity)


class AMPolygonPrimitive(AMPrimitive):
    """ Aperture Macro Polygon primitive. Code 5.

    A polygon primitive is a regular polygon defined by the number of
    vertices, the center point, and the diameter of the circumscribed circle.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.8:** Polygon, primitive code 5.

    Parameters
    ----------
    code : int
        PolygonPrimitive code. Must be 5.

    exposure : string
        'on' or 'off'

    vertices : int, 3 <= vertices <= 12
        Number of vertices

    position : tuple (<float>, <float>)
        X and Y coordinates of polygon center

    diameter : float
        diameter of circumscribed circle.

    rotation : float
        polygon rotation about the origin.

    Returns
    -------
    PolygonPrimitive : :class:`gerber.am_statements.AMPolygonPrimitive`
        An initialized AMPolygonPrimitive

    Raises
    ------
    ValueError, TypeError
    """

    @classmethod
    def from_primitive(cls, primitive):
        return cls(5, 'on', primitive.sides, primitive.position, primitive.diameter, primitive.rotation)

    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")
        code = int(modifiers[0])
        exposure = "on" if float(modifiers[1]) == 1 else "off"
        vertices = int(float(modifiers[2]))
        position = (float(modifiers[3]), float(modifiers[4]))
        try:
            diameter = float(modifiers[5])
        except:
            diameter = 0

        rotation = float(modifiers[6])
        return cls(code, exposure, vertices, position, diameter, rotation)

    def __init__(self, code, exposure, vertices, position, diameter, rotation):
        """ Initialize AMPolygonPrimitive
        """
        if code != 5:
            raise ValueError('PolygonPrimitive code is 5')
        super(AMPolygonPrimitive, self).__init__(code, exposure)
        if vertices < 3 or vertices > 12:
            raise ValueError('Number of vertices must be between 3 and 12')
        self.vertices = vertices
        validate_coordinates(position)
        self.position = position
        self.diameter = diameter
        self.rotation = rotation

    def to_inch(self):
        self.position = tuple([inch(x) for x in self.position])
        self.diameter = inch(self.diameter)

    def to_metric(self):
        self.position = tuple([metric(x) for x in self.position])
        self.diameter = metric(self.diameter)

    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            exposure="1" if self.exposure == "on" else "0",
            vertices=self.vertices,
            position="%.4g,%.4g" % self.position,
            diameter='%.4g' % self.diameter,
            rotation=str(self.rotation)
        )
        fmt = "{code},{exposure},{vertices},{position},{diameter},{rotation}*"
        return fmt.format(**data)

    def to_primitive(self, units):
        return Polygon(self.position, self.vertices, self.diameter / 2.0, 0, rotation=self.rotation, units=units, level_polarity=self._level_polarity)


class AMMoirePrimitive(AMPrimitive):
    """ Aperture Macro Moire primitive. Code 6.

    The moire primitive is a cross hair centered on concentric rings (annuli).
    Exposure is always on.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.9:** Moire, primitive code 6.

    Parameters
    ----------
    code : int
        Moire Primitive code. Must be 6.

    position : tuple (<float>, <float>)
        X and Y coordinates of moire center

    diameter : float
        outer diameter of outer ring.

    ring_thickness : float
        thickness of concentric rings.

    gap : float
        gap between concentric rings.

    max_rings : float
        maximum number of rings

    crosshair_thickness : float
        thickness of crosshairs

    crosshair_length : float
        length of crosshairs

    rotation : float
        moire rotation about the origin.

    Returns
    -------
    MoirePrimitive : :class:`gerber.am_statements.AMMoirePrimitive`
        An initialized AMMoirePrimitive

    Raises
    ------
    ValueError, TypeError
    """
    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")
        code = int(modifiers[0])
        position = (float(modifiers[1]), float(modifiers[2]))
        diameter = float(modifiers[3])
        ring_thickness = float(modifiers[4])
        gap = float(modifiers[5])
        max_rings = int(float(modifiers[6]))
        crosshair_thickness = float(modifiers[7])
        crosshair_length = float(modifiers[8])
        rotation = float(modifiers[9])
        return cls(code, position, diameter, ring_thickness, gap, max_rings, crosshair_thickness, crosshair_length, rotation)

    def __init__(self, code, position, diameter, ring_thickness, gap, max_rings, crosshair_thickness, crosshair_length, rotation):
        """ Initialize AMoirePrimitive
        """
        if code != 6:
            raise ValueError('MoirePrimitive code is 6')
        super(AMMoirePrimitive, self).__init__(code, 'on')
        validate_coordinates(position)
        self.position = position
        self.diameter = diameter
        self.ring_thickness = ring_thickness
        self.gap = gap
        self.max_rings = max_rings
        self.crosshair_thickness = crosshair_thickness
        self.crosshair_length = crosshair_length
        self.rotation = rotation

    def to_inch(self):
        self.position = tuple([inch(x) for x in self.position])
        self.diameter = inch(self.diameter)
        self.ring_thickness = inch(self.ring_thickness)
        self.gap = inch(self.gap)
        self.crosshair_thickness = inch(self.crosshair_thickness)
        self.crosshair_length = inch(self.crosshair_length)

    def to_metric(self):
        self.position = tuple([metric(x) for x in self.position])
        self.diameter = metric(self.diameter)
        self.ring_thickness = metric(self.ring_thickness)
        self.gap = metric(self.gap)
        self.crosshair_thickness = metric(self.crosshair_thickness)
        self.crosshair_length = metric(self.crosshair_length)


    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            position="%.4g,%.4g" % self.position,
            diameter=self.diameter,
            ring_thickness=self.ring_thickness,
            gap=self.gap,
            max_rings=self.max_rings,
            crosshair_thickness=self.crosshair_thickness,
            crosshair_length=self.crosshair_length,
            rotation=self.rotation
        )
        fmt = "{code},{position},{diameter},{ring_thickness},{gap},{max_rings},{crosshair_thickness},{crosshair_length},{rotation}*"
        return fmt.format(**data)

    def to_primitive(self, units):
        #raise NotImplementedError()
        return None


class AMThermalPrimitive(AMPrimitive):
    """ Aperture Macro Thermal primitive. Code 7.

    The thermal primitive is a ring (annulus) interrupted by four gaps.
    Exposure is always on.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.10:** Thermal, primitive code 7.

    Parameters
    ----------
    code : int
        Thermal Primitive code. Must be 7.

    position : tuple (<float>, <float>)
        X and Y coordinates of thermal center

    outer_diameter : float
        outer diameter of thermal.

    inner_diameter : float
        inner diameter of thermal.

    gap : float
        gap thickness

    rotation : float
        thermal rotation about the origin.

    Returns
    -------
    ThermalPrimitive : :class:`gerber.am_statements.AMThermalPrimitive`
        An initialized AMThermalPrimitive

    Raises
    ------
    ValueError, TypeError
    """
    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")
        code = int(modifiers[0])
        position = (float(modifiers[1]), float(modifiers[2]))
        outer_diameter = float(modifiers[3])
        inner_diameter = float(modifiers[4])
        gap = float(modifiers[5])
        rotation = float(modifiers[6])
        return cls(code, position, outer_diameter, inner_diameter, gap, rotation)

    def __init__(self, code, position, outer_diameter, inner_diameter, gap, rotation):
        if code != 7:
            raise ValueError('ThermalPrimitive code is 7')
        super(AMThermalPrimitive, self).__init__(code, 'on')
        validate_coordinates(position)
        self.position = position
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
        self.gap = gap
        self.rotation = rotation

    def to_inch(self):
        self.position = tuple([inch(x) for x in self.position])
        self.outer_diameter = inch(self.outer_diameter)
        self.inner_diameter = inch(self.inner_diameter)
        self.gap = inch(self.gap)

    def to_metric(self):
        self.position = tuple([metric(x) for x in self.position])
        self.outer_diameter = metric(self.outer_diameter)
        self.inner_diameter = metric(self.inner_diameter)
        self.gap = metric(self.gap)

    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            position="%.4g,%.4g" % self.position,
            outer_diameter=self.outer_diameter,
            inner_diameter=self.inner_diameter,
            gap=self.gap,
            rotation=self.rotation
        )
        fmt = "{code},{position},{outer_diameter},{inner_diameter},{gap},{rotation}*"
        return fmt.format(**data)

    def _approximate_arc_cw(self, start_angle, end_angle, radius, center):
        """
        Get an arc as a series of points

        Parameters
        ----------
        start_angle : The start angle in radians
        end_angle : The end angle in radians
        radius`: Radius of the arc
        center : The center point of the arc (x, y) tuple

        Returns
        -------
        array of point tuples
        """

        # The total sweep
        sweep_angle = end_angle - start_angle
        num_steps = 10

        angle_step = sweep_angle / num_steps

        radius = radius
        center = center

        points = []

        for i in range(num_steps + 1):
            current_angle = start_angle + (angle_step * i)

            nextx = (center[0] + math.cos(current_angle) * radius)
            nexty = (center[1] + math.sin(current_angle) * radius)

            points.append((nextx, nexty))

        return points

    def to_primitive(self, units):

        # We start with calculating the top right section, then duplicate it

        inner_radius = self.inner_diameter / 2.0
        outer_radius = self.outer_diameter / 2.0

        # Calculate the start angle relative to the horizontal axis
        inner_offset_angle = asin(self.gap / 2.0 / inner_radius)
        outer_offset_angle = asin(self.gap / 2.0 / outer_radius)

        rotation_rad = math.radians(self.rotation)
        inner_start_angle = inner_offset_angle + rotation_rad
        inner_end_angle =  math.pi / 2 - inner_offset_angle + rotation_rad

        outer_start_angle = outer_offset_angle + rotation_rad
        outer_end_angle = math.pi / 2 - outer_offset_angle + rotation_rad

        outlines = []
        aperture = Circle((0, 0), 0)

        points = (self._approximate_arc_cw(inner_start_angle, inner_end_angle, inner_radius, self.position)
                + list(reversed(self._approximate_arc_cw(outer_start_angle, outer_end_angle, outer_radius, self.position))))
        # Add in the last point since outlines should be closed
        points.append(points[0])

        # There are four outlines at rotated sections
        for rotation in [0, 90.0, 180.0, 270.0]:

            lines = []
            prev_point = rotate_point(points[0], rotation, self.position)
            for point in points[1:]:
                cur_point = rotate_point(point, rotation, self.position)

                lines.append(Line(prev_point, cur_point, aperture))

            prev_point = cur_point

            outlines.append(Outline(lines, units=units, level_polarity=self._level_polarity))

        return outlines


class AMCenterLinePrimitive(AMPrimitive):
    """ Aperture Macro Center Line primitive. Code 21.

    The center line primitive is a rectangle defined by its width, height, and center point.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.4:** Center Line, primitive code 21.

    Parameters
    ----------
    code : int
        Center Line Primitive code. Must be 21.

    exposure : str
        'on' or 'off'

    width : float
        Width of rectangle

    height : float
        Height of rectangle

    center : tuple (<float>, <float>)
        X and Y coordinates of line center

    rotation : float
        rectangle rotation about its center.

    Returns
    -------
    CenterLinePrimitive : :class:`gerber.am_statements.AMCenterLinePrimitive`
        An initialized AMCenterLinePrimitive

    Raises
    ------
    ValueError, TypeError
    """

    @classmethod
    def from_primitive(cls, primitive):
        width = primitive.width
        height = primitive.height
        center = primitive.position
        rotation = math.degrees(primitive.rotation)
        return cls(21, 'on', width, height, center, rotation)

    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")
        code = int(modifiers[0])
        exposure = 'on' if float(modifiers[1]) == 1 else 'off'
        width = float(modifiers[2])
        height = float(modifiers[3])
        center = (float(modifiers[4]), float(modifiers[5]))
        rotation = float(modifiers[6])
        return cls(code, exposure, width, height, center, rotation)

    def __init__(self, code, exposure, width, height, center, rotation):
        if code != 21:
            raise ValueError('CenterLinePrimitive code is 21')
        super(AMCenterLinePrimitive, self).__init__(code, exposure)
        self.width = width
        self.height = height
        validate_coordinates(center)
        self.center = center
        self.rotation = rotation

    def to_inch(self):
        self.center = tuple([inch(x) for x in self.center])
        self.width = inch(self.width)
        self.height = inch(self.height)

    def to_metric(self):
        self.center = tuple([metric(x) for x in self.center])
        self.width = metric(self.width)
        self.height = metric(self.height)

    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            exposure = '1' if self.exposure == 'on' else '0',
            width = self.width,
            height = self.height,
            center="%.4g,%.4g" % self.center,
            rotation=self.rotation
        )
        fmt = "{code},{exposure},{width},{height},{center},{rotation}*"
        return fmt.format(**data)

    def to_primitive(self, units):

        x = self.center[0]
        y = self.center[1]
        half_width = self.width / 2.0
        half_height = self.height / 2.0

        points = []
        points.append((x - half_width, y + half_height))
        points.append((x - half_width, y - half_height))
        points.append((x + half_width, y - half_height))
        points.append((x + half_width, y + half_height))

        aperture = Circle((0, 0), 0)

        lines = []
        prev_point = rotate_point(points[3], self.rotation, self.center)
        for point in points:
            cur_point = rotate_point(point, self.rotation, self.center)

            lines.append(Line(prev_point, cur_point, aperture))

        return Outline(lines, units=units, level_polarity=self._level_polarity)


class AMLowerLeftLinePrimitive(AMPrimitive):
    """ Aperture Macro Lower Left Line primitive. Code 22.

    The lower left line primitive is a rectangle defined by its width, height, and the lower left point.

    .. seealso::
        `The Gerber File Format Specification <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_
            **Section 4.12.3.5:** Lower Left Line, primitive code 22.

    Parameters
    ----------
    code : int
        Center Line Primitive code. Must be 22.

    exposure : str
        'on' or 'off'

    width : float
        Width of rectangle

    height : float
        Height of rectangle

    lower_left : tuple (<float>, <float>)
        X and Y coordinates of lower left corner

    rotation : float
        rectangle rotation about its origin.

    Returns
    -------
    LowerLeftLinePrimitive : :class:`gerber.am_statements.AMLowerLeftLinePrimitive`
        An initialized AMLowerLeftLinePrimitive

    Raises
    ------
    ValueError, TypeError
    """
    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")
        code = int(modifiers[0])
        exposure = 'on' if float(modifiers[1]) == 1 else 'off'
        width = float(modifiers[2])
        height = float(modifiers[3])
        lower_left = (float(modifiers[4]), float(modifiers[5]))
        rotation = float(modifiers[6])
        return cls(code, exposure, width, height, lower_left, rotation)

    def __init__(self, code, exposure, width, height, lower_left, rotation):
        if code != 22:
            raise ValueError('LowerLeftLinePrimitive code is 22')
        super (AMLowerLeftLinePrimitive, self).__init__(code, exposure)
        self.width = width
        self.height = height
        validate_coordinates(lower_left)
        self.lower_left = lower_left
        self.rotation = rotation

    def to_inch(self):
        self.lower_left = tuple([inch(x) for x in self.lower_left])
        self.width = inch(self.width)
        self.height = inch(self.height)

    def to_metric(self):
        self.lower_left = tuple([metric(x) for x in self.lower_left])
        self.width = metric(self.width)
        self.height = metric(self.height)

    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            exposure = '1' if self.exposure == 'on' else '0',
            width = self.width,
            height = self.height,
            lower_left="%.4g,%.4g" % self.lower_left,
            rotation=self.rotation
        )
        fmt = "{code},{exposure},{width},{height},{lower_left},{rotation}*"
        return fmt.format(**data)


class AMUnsupportPrimitive(AMPrimitive):
    @classmethod
    def from_gerber(cls, primitive):
        return cls(primitive)

    def __init__(self, primitive):
        super(AMUnsupportPrimitive, self).__init__(9999)
        self.primitive = primitive

    def to_inch(self):
        pass

    def to_metric(self):
        pass

    def to_gerber(self, settings=None):
        return self.primitive
