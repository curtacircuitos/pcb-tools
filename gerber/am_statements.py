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

from .utils import validate_coordinates


# TODO: Add support for aperture macro variables

class AMPrimitive(object):
    """ Aperture Macro Primitive Base Class
    """
    def __init__(self, code, exposure=None):
        """ Initialize Aperture Macro Primitive base class

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
        VALID_CODES = (0, 1, 2, 4, 5, 6, 7, 20, 21, 22)
        if not isinstance(code, int):
            raise TypeError('Aperture Macro Primitive code must be an integer')
        elif code not in VALID_CODES:
            raise ValueError('Invalid Code. Valid codes are %s.' % ', '.join(map(str, VALID_CODES)))
        if exposure is not None and exposure.lower() not in ('on', 'off'):
            raise ValueError('Exposure must be either on or off')
        self.code = code
        self.exposure = exposure.lower() if exposure is not None else None

    def to_inch(self):
        pass

    def to_metric(self):
        pass


class AMCommentPrimitive(AMPrimitive):
    """ Aperture Macro Comment primitive. Code 0
    """
    @classmethod
    def from_gerber(cls, primitive):
        primitive = primitive.strip()
        code = int(primitive[0])
        comment = primitive[1:]
        return cls(code, comment)

    def __init__(self, code, comment):
        """ Initialize AMCommentPrimitive class

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
        if code != 0:
            raise ValueError('Not a valid Aperture Macro Comment statement')
        super(AMCommentPrimitive, self).__init__(code)
        self.comment = comment.strip(' *')

    def to_gerber(self, settings=None):
        return '0 %s *' % self.comment

    def __str__(self):
        return '<Aperture Macro Comment: %s>' % self.comment


class AMCirclePrimitive(AMPrimitive):
    """ Aperture macro Circle primitive. Code 1
    """
    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(',')
        code = int(modifiers[0])
        exposure = 'on' if modifiers[1].strip() == '1' else 'off'
        diameter = float(modifiers[2])
        position = (float(modifiers[3]), float(modifiers[4]))
        return cls(code, exposure, diameter, position)

    def __init__(self, code, exposure, diameter, position):
        """ Initialize AMCirclePrimitive

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
        validate_coordinates(position)
        if code != 1:
            raise ValueError('Not a valid Aperture Macro Circle statement')
        super(AMCirclePrimitive, self).__init__(code, exposure)
        self.diameter = diameter
        self.position = position

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    exposure = '1' if self.exposure == 'on' else 0,
                    diameter = self.diameter,
                    x = self.position[0],
                    y = self.position[1])
        return '{code},{exposure},{diameter},{x},{y}*'.format(**data)


class AMVectorLinePrimitive(AMPrimitive):
    """ Aperture Macro Vector Line primitive. Code 2 or 20
    """
    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(',')
        code = int(modifiers[0])
        exposure = 'on' if modifiers[1].strip() == '1' else 'off'
        width = float(modifiers[2])
        start (float(modifiers[3]), float(modifiers[4]))
        end = (float(modifiers[5]), float(modifiers[6]))
        rotation = float(modifiers[7])
        return cls(code, exposure, width, start, end, rotation)

    def __init__(self, code, exposure, width, start, end, rotation):
        """ Initialize AMVectorLinePrimitive

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
        validate_coordinates(start)
        validate_coordinates(end)
        if code not in (2, 20):
            raise ValueError('Valid VectorLinePrimitive codes are 2 or 20')
        super(AMVectorLinePrimitive, self).__init__(code, exposure)
        self.width = width
        self.start = start
        self.end = end
        self.rotation = rotation

    def to_gerber(self, settings=None):
        fmtstr = '{code},{exp},{width},{startx},{starty},{endx},{endy},{rot}*'
        data = dict(code = self.code,
                    exp = 1 if self.exposure == 'on' else 0,
                    startx = self.start[0],
                    starty = self.start[1],
                    endx = self.end[0],
                    endy = self.end[1],
                    rotation = self.rotation)
        return fmtstr.format(**data)

# Code 4
class AMOutlinePrimitive(AMPrimitive):

    @classmethod
    def from_gerber(cls, primitive):
        modifiers = primitive.strip(' *').split(",")

        code = int(modifiers[0])
        exposure = "on" if modifiers[1].strip() == "1" else "off"
        n = int(modifiers[2])
        start_point = (float(modifiers[3]), float(modifiers[4]))
        points = []

        for i in range(n):
            points.append((float(modifiers[5 + i*2]), float(modifiers[5 + i*2 + 1])))

        rotation = float(modifiers[-1])

        return cls(code, exposure, start_point, points, rotation)

    def __init__(self, code, exposure, start_point, points, rotation):
        """ Initialize AMOutlinePrimitive

        Parameters
        ----------
        code : int
            OutlinePrimitive code. Must be 4.

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
        validate_coordinates(start_point)
        for point in points:
            validate_coordinates(point)
        super(AMOutlinePrimitive, self).__init__(code, exposure)
        self.start_point = start_point
        self.points = points
        self.rotation = rotation

    def to_inch(self):
        self.start_point = tuple([x / 25.4 for x in self.start_point])
        self.points = tuple([(x / 25.4, y / 25.4) for x, y in self.points])

    def to_metric(self):
        self.start_point = tuple([x * 25.4 for x in self.start_point])
        self.points = tuple([(x * 25.4, y * 25.4) for x, y in self.points])

    def to_gerber(self, settings=None):
        data = dict(
            code=self.code,
            exposure="1" if self.exposure == "on" else "0",
            n_points=len(self.points),
            start_point="%.4f,%.4f" % self.start_point,
            points=",".join(["%.4f,%.4f" % point for point in self.points]),
            rotation=str(self.rotation)
        )
        return "{code},{exposure},{n_points},{start_point},{points},{rotation}*".format(**data)

# Code 5
class AMPolygonPrimitive(AMPrimitive):
    pass


# Code 6
class AMMoirePrimitive(AMPrimitive):
    pass


# Code 7
class AMThermalPrimitive(AMPrimitive):
    pass


# Code 21
class AMCenterLinePrimitive(AMPrimitive):
    pass


# Code 22
class AMLowerLeftLinePrimitive(AMPrimitive):
    pass


class AMUnsupportPrimitive(AMPrimitive):
    @classmethod
    def from_gerber(cls, primitive):
        return cls(primitive)

    def __init__(self, primitive):
        self.primitive = primitive

    def to_gerber(self, settings=None):
        return self.primitive
