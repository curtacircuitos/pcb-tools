#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math
from operator import add, sub
from copy import deepcopy

from .utils import validate_coordinates, inch, metric


class Primitive(object):
    """ Base class for all Cam file primitives

    Parameters
    ---------
    level_polarity : string
        Polarity of the parameter. May be 'dark' or 'clear'. Dark indicates
        a "positive" primitive, i.e. indicating where coppper should remain,
        and clear indicates a negative primitive, such as where copper should
        be removed. clear primitives are often used to create cutouts in region
        pours.

    rotation : float
        Rotation of a primitive about its origin in degrees. Positive rotation
        is counter-clockwise as viewed from the board top.
    """
    def __init__(self, level_polarity='dark', rotation=0, units=None, id=None, statement_id=None):
        self.level_polarity = level_polarity
        self.rotation = rotation
        self.units = units
        self._to_convert = list()
        self.id = id
        self.statement_id = statement_id

    def bounding_box(self):
        """ Calculate bounding box

        will be helpful for sweep & prune during DRC clearance checks.

        Return ((min x, max x), (min y, max y))
        """
        raise NotImplementedError('Bounding box calculation must be '
                                  'implemented in subclass')

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            for attr, value in [(attr, getattr(self, attr)) for attr in self._to_convert]:
                if hasattr(value, 'to_inch'):
                    value.to_inch()
                else:
                    try:
                        if len(value) > 1:
                            if hasattr(value[0], 'to_inch'):
                                for v in value:
                                    v.to_inch()
                            elif isinstance(value[0], tuple):
                                setattr(self, attr, [tuple(map(inch, point)) for point in value])
                            else:
                                setattr(self, attr, tuple(map(inch, value)))
                    except:
                        if value is not None:
                            setattr(self, attr, inch(value))


    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            for attr, value in [(attr, getattr(self, attr)) for attr in self._to_convert]:
                if hasattr(value, 'to_metric'):
                    value.to_metric()
                else:
                    try:
                        if len(value) > 1:
                            if hasattr(value[0], 'to_metric'):
                                for v in value:
                                    v.to_metric()
                            elif isinstance(value[0], tuple):
                                setattr(self, attr, [tuple(map(metric, point)) for point in value])
                            else:
                                setattr(self, attr, tuple(map(metric, value)))
                    except:
                        if value is not None:
                            setattr(self, attr, metric(value))

    def offset(self, x_offset=0, y_offset=0):
        pass

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Line(Primitive):
    """
    """
    def __init__(self, start, end, aperture, **kwargs):
        super(Line, self).__init__(**kwargs)
        self.start = start
        self.end = end
        self.aperture = aperture
        self._to_convert = ['start', 'end', 'aperture']

    @property
    def reversed(self):
        rline = deepcopy(self)
        rline.start = self.end
        rline.end = self.start
        return rline

    @property
    def angle(self):
        delta_x, delta_y = tuple(map(sub, self.end, self.start))
        angle = math.atan2(delta_y, delta_x)
        return angle

    @property
    def bounding_box(self):
        if isinstance(self.aperture, Circle):
            width_2 = self.aperture.radius
            height_2 = width_2
        else:
            width_2 = self.aperture.width / 2.
            height_2 = self.aperture.height / 2.
        min_x = min(self.start[0], self.end[0]) - width_2
        max_x = max(self.start[0], self.end[0]) + width_2
        min_y = min(self.start[1], self.end[1]) - height_2
        max_y = max(self.start[1], self.end[1]) + height_2
        return ((min_x, max_x), (min_y, max_y))

    @property
    def vertices(self):
        if not isinstance(self.aperture, Rectangle):
            return None
        else:
            start = self.start
            end = self.end
            width = self.aperture.width
            height = self.aperture.height

            # Find all the corners of the start and end position
            start_ll = (start[0] - (width / 2.),
                        start[1] - (height / 2.))
            start_lr = (start[0] + (width / 2.),
                        start[1] - (height / 2.))
            start_ul = (start[0] - (width / 2.),
                        start[1] + (height / 2.))
            start_ur = (start[0] + (width / 2.),
                        start[1] + (height / 2.))
            end_ll = (end[0] - (width / 2.),
                      end[1] - (height / 2.))
            end_lr = (end[0] + (width / 2.),
                      end[1] - (height / 2.))
            end_ul = (end[0] - (width / 2.),
                      end[1] + (height / 2.))
            end_ur = (end[0] + (width / 2.),
                      end[1] + (height / 2.))

            if end[0] == start[0] and end[1] == start[1]:
                return (start_ll, start_lr, start_ur, start_ul)
            elif end[0] == start[0] and end[1] > start[1]:
                return (start_ll, start_lr, end_ur, end_ul)
            elif end[0] > start[0] and end[1] > start[1]:
                return (start_ll, start_lr, end_lr, end_ur, end_ul, start_ul)
            elif end[0] > start[0] and end[1] == start[1]:
                return (start_ll, end_lr, end_ur, start_ul)
            elif end[0] > start[0] and end[1] < start[1]:
                return (start_ll, end_ll, end_lr, end_ur, start_ur, start_ul)
            elif end[0] == start[0] and end[1] < start[1]:
                return (end_ll, end_lr, start_ur, start_ul)
            elif end[0] < start[0] and end[1] < start[1]:
                return (end_ll, end_lr, start_lr, start_ur, start_ul, end_ul)
            elif end[0] < start[0] and end[1] == start[1]:
                return (end_ll, start_lr, start_ur, end_ul)
            elif end[0] < start[0] and end[1] > start[1]:
                return (start_ll, start_lr, start_ur, end_ur, end_ul, end_ll)


    def offset(self, x_offset=0, y_offset=0):
        self.start = tuple(map(add, self.start, (x_offset, y_offset)))
        self.end = tuple(map(add, self.end, (x_offset, y_offset)))


class Arc(Primitive):
    """
    """
    def __init__(self, start, end, center, direction, aperture, **kwargs):
        super(Arc, self).__init__(**kwargs)
        self.start = start
        self.end = end
        self.center = center
        self.direction = direction
        self.aperture = aperture
        self._to_convert = ['start', 'end', 'center', 'aperture']

    @property
    def radius(self):
        dy, dx = map(sub, self.start, self.center)
        return math.sqrt(dy**2 + dx**2)

    @property
    def start_angle(self):
        dy, dx = map(sub, self.start, self.center)
        return math.atan2(dx, dy)

    @property
    def end_angle(self):
        dy, dx = map(sub, self.end, self.center)
        return math.atan2(dx, dy)

    @property
    def sweep_angle(self):
        two_pi = 2 * math.pi
        theta0 = (self.start_angle + two_pi) % two_pi
        theta1 = (self.end_angle + two_pi) % two_pi
        if self.direction == 'counterclockwise':
            return abs(theta1 - theta0)
        else:
            theta0 += two_pi
            return abs(theta0 - theta1) % two_pi

    @property
    def bounding_box(self):
        two_pi = 2 * math.pi
        theta0 = (self.start_angle + two_pi) % two_pi
        theta1 = (self.end_angle + two_pi) % two_pi
        points = [self.start, self.end]
        if self.direction == 'counterclockwise':
            # Passes through 0 degrees
            if theta0 > theta1:
                points.append((self.center[0] + self.radius, self.center[1]))
            # Passes through 90 degrees
            if theta0 <= math.pi / 2. and (theta1 >= math.pi / 2. or theta1 < theta0):
                points.append((self.center[0], self.center[1] + self.radius))
            # Passes through 180 degrees
            if theta0 <= math.pi and (theta1 >= math.pi or theta1 < theta0):
                points.append((self.center[0] - self.radius, self.center[1]))
            # Passes through 270 degrees
            if theta0 <= math.pi * 1.5 and (theta1 >= math.pi * 1.5 or theta1 < theta0):
                points.append((self.center[0], self.center[1] - self.radius ))
        else:
             # Passes through 0 degrees
            if theta1 > theta0:
                points.append((self.center[0] + self.radius, self.center[1]))
            # Passes through 90 degrees
            if theta1 <= math.pi / 2. and (theta0 >= math.pi / 2. or theta0 < theta1):
                points.append((self.center[0], self.center[1] + self.radius))
            # Passes through 180 degrees
            if theta1 <= math.pi and (theta0 >= math.pi or theta0 < theta1):
                points.append((self.center[0] - self.radius, self.center[1]))
            # Passes through 270 degrees
            if theta1 <= math.pi * 1.5 and (theta0 >= math.pi * 1.5 or theta0 < theta1):
                points.append((self.center[0], self.center[1] - self.radius ))
        x, y = zip(*points)
        min_x = min(x) - self.aperture.radius
        max_x = max(x) + self.aperture.radius
        min_y = min(y) - self.aperture.radius
        max_y = max(y) + self.aperture.radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.start = tuple(map(add, self.start, (x_offset, y_offset)))
        self.end = tuple(map(add, self.end, (x_offset, y_offset)))
        self.center = tuple(map(add, self.center, (x_offset, y_offset)))


class Circle(Primitive):
    """
    """
    def __init__(self, position, diameter, **kwargs):
        super(Circle, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.diameter = diameter
        self._to_convert = ['position', 'diameter']

    @property
    def radius(self):
        return self.diameter / 2.

    @property
    def bounding_box(self):
        min_x = self.position[0] - self.radius
        max_x = self.position[0] + self.radius
        min_y = self.position[1] - self.radius
        max_y = self.position[1] + self.radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))


class Ellipse(Primitive):
    """
    """
    def __init__(self, position, width, height, **kwargs):
        super(Ellipse, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.width = width
        self.height = height
        self._to_convert = ['position', 'width', 'height']


    @property
    def bounding_box(self):
        min_x = self.position[0] - (self._abs_width / 2.0)
        max_x = self.position[0] + (self._abs_width / 2.0)
        min_y = self.position[1] - (self._abs_height / 2.0)
        max_y = self.position[1] + (self._abs_height / 2.0)
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def _abs_width(self):
        ux = (self.width / 2.) * math.cos(math.radians(self.rotation))
        vx = (self.height / 2.) * math.cos(math.radians(self.rotation) + (math.pi / 2.))
        return 2 * math.sqrt((ux * ux) + (vx * vx))

    @property
    def _abs_height(self):
        uy = (self.width / 2.) * math.sin(math.radians(self.rotation))
        vy = (self.height / 2.) * math.sin(math.radians(self.rotation) + (math.pi / 2.))
        return 2 * math.sqrt((uy * uy) + (vy * vy))


class Rectangle(Primitive):
    """
    """
    def __init__(self, position, width, height, **kwargs):
        super(Rectangle, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.width = width
        self.height = height
        self._to_convert = ['position', 'width', 'height']


    @property
    def lower_left(self):
        return (self.position[0] - (self._abs_width / 2.),
                self.position[1] - (self._abs_height / 2.))

    @property
    def upper_right(self):
        return (self.position[0] + (self._abs_width / 2.),
                self.position[1] + (self._abs_height / 2.))

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def _abs_width(self):
        return (math.cos(math.radians(self.rotation)) * self.width +
                math.sin(math.radians(self.rotation)) * self.height)
    @property
    def _abs_height(self):
        return (math.cos(math.radians(self.rotation)) * self.height +
                math.sin(math.radians(self.rotation)) * self.width)


class Diamond(Primitive):
    """
    """
    def __init__(self, position, width, height, **kwargs):
        super(Diamond, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.width = width
        self.height = height
        self._to_convert = ['position', 'width', 'height']

    @property
    def lower_left(self):
        return (self.position[0] - (self._abs_width / 2.),
                self.position[1] - (self._abs_height / 2.))

    @property
    def upper_right(self):
        return (self.position[0] + (self._abs_width / 2.),
                self.position[1] + (self._abs_height / 2.))

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def _abs_width(self):
        return (math.cos(math.radians(self.rotation)) * self.width +
                math.sin(math.radians(self.rotation)) * self.height)
    @property
    def _abs_height(self):
        return (math.cos(math.radians(self.rotation)) * self.height +
                math.sin(math.radians(self.rotation)) * self.width)


class ChamferRectangle(Primitive):
    """
    """
    def __init__(self, position, width, height, chamfer, corners, **kwargs):
        super(ChamferRectangle, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.width = width
        self.height = height
        self.chamfer = chamfer
        self.corners = corners
        self._to_convert = ['position', 'width', 'height', 'chamfer']

    @property
    def lower_left(self):
        return (self.position[0] - (self._abs_width / 2.),
                self.position[1] - (self._abs_height / 2.))

    @property
    def upper_right(self):
        return (self.position[0] + (self._abs_width / 2.),
                self.position[1] + (self._abs_height / 2.))

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def _abs_width(self):
        return (math.cos(math.radians(self.rotation)) * self.width +
                math.sin(math.radians(self.rotation)) * self.height)
    @property
    def _abs_height(self):
        return (math.cos(math.radians(self.rotation)) * self.height +
                math.sin(math.radians(self.rotation)) * self.width)

class RoundRectangle(Primitive):
    """
    """
    def __init__(self, position, width, height, radius, corners, **kwargs):
        super(RoundRectangle, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.width = width
        self.height = height
        self.radius = radius
        self.corners = corners
        self._to_convert = ['position', 'width', 'height', 'radius']

    @property
    def lower_left(self):
        return (self.position[0] - (self._abs_width / 2.),
                self.position[1] - (self._abs_height / 2.))

    @property
    def upper_right(self):
        return (self.position[0] + (self._abs_width / 2.),
                self.position[1] + (self._abs_height / 2.))

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def _abs_width(self):
        return (math.cos(math.radians(self.rotation)) * self.width +
                math.sin(math.radians(self.rotation)) * self.height)
    @property
    def _abs_height(self):
        return (math.cos(math.radians(self.rotation)) * self.height +
                math.sin(math.radians(self.rotation)) * self.width)

class Obround(Primitive):
    """
    """
    def __init__(self, position, width, height, **kwargs):
        super(Obround, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.width = width
        self.height = height
        self._to_convert = ['position', 'width', 'height']

    @property
    def lower_left(self):
        return (self.position[0] - (self._abs_width / 2.),
                self.position[1] - (self._abs_height / 2.))

    @property
    def upper_right(self):
        return (self.position[0] + (self._abs_width / 2.),
                self.position[1] + (self._abs_height / 2.))

    @property
    def orientation(self):
        return 'vertical' if self.height > self.width else 'horizontal'

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    @property
    def subshapes(self):
        if self.orientation == 'vertical':
            circle1 = Circle((self.position[0], self.position[1] +
                              (self.height-self.width) / 2.), self.width)
            circle2 = Circle((self.position[0], self.position[1] -
                              (self.height-self.width) / 2.), self.width)
            rect = Rectangle(self.position, self.width,
                            (self.height - self.width))
        else:
            circle1 = Circle((self.position[0] - (self.height - self.width) / 2.,
                              self.position[1]), self.height)
            circle2 = Circle((self.position[0] + (self.height - self.width) / 2.,
                              self.position[1]), self.height)
            rect = Rectangle(self.position, (self.width - self.height),
                            self.height)
        return {'circle1': circle1, 'circle2': circle2, 'rectangle': rect}

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def _abs_width(self):
        return (math.cos(math.radians(self.rotation)) * self.width +
                math.sin(math.radians(self.rotation)) * self.height)
    @property
    def _abs_height(self):
        return (math.cos(math.radians(self.rotation)) * self.height +
                math.sin(math.radians(self.rotation)) * self.width)

class Polygon(Primitive):
    """
    """
    def __init__(self, position, sides, radius, **kwargs):
        super(Polygon, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.sides = sides
        self.radius = radius
        self._to_convert = ['position', 'radius']

    @property
    def bounding_box(self):
        min_x = self.position[0] - self.radius
        max_x = self.position[0] + self.radius
        min_y = self.position[1] - self.radius
        max_y = self.position[1] + self.radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))


class Region(Primitive):
    """
    """
    def __init__(self, primitives, **kwargs):
        super(Region, self).__init__(**kwargs)
        self.primitives = primitives
        self._to_convert = ['primitives']

    @property
    def bounding_box(self):
        xlims, ylims = zip(*[p.bounding_box for p in self.primitives])
        minx, maxx = zip(*xlims)
        miny, maxy = zip(*ylims)
        min_x = min(minx)
        max_x = max(maxx)
        min_y = min(miny)
        max_y = max(maxy)
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        for p in self.primitives:
            p.offset(x_offset, y_offset)


class RoundButterfly(Primitive):
    """ A circle with two diagonally-opposite quadrants removed
    """
    def __init__(self, position, diameter, **kwargs):
        super(RoundButterfly, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.diameter = diameter
        self._to_convert = ['position', 'diameter']

    @property
    def radius(self):
        return self.diameter / 2.

    @property
    def bounding_box(self):
        min_x = self.position[0] - self.radius
        max_x = self.position[0] + self.radius
        min_y = self.position[1] - self.radius
        max_y = self.position[1] + self.radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))


class SquareButterfly(Primitive):
    """ A square with two diagonally-opposite quadrants removed
    """
    def __init__(self, position, side, **kwargs):
        super(SquareButterfly, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.side = side
        self._to_convert = ['position', 'side']


    @property
    def bounding_box(self):
        min_x = self.position[0] - (self.side / 2.)
        max_x = self.position[0] + (self.side / 2.)
        min_y = self.position[1] - (self.side / 2.)
        max_y = self.position[1] + (self.side / 2.)
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))


class Donut(Primitive):
    """ A Shape with an identical concentric shape removed from its center
    """
    def __init__(self, position, shape, inner_diameter, outer_diameter, **kwargs):
        super(Donut, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        if shape not in ('round', 'square', 'hexagon', 'octagon'):
            raise ValueError('Valid shapes are round, square, hexagon or octagon')
        self.shape = shape
        if inner_diameter >= outer_diameter:
            raise ValueError('Outer diameter must be larger than inner diameter.')
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        if self.shape in ('round', 'square', 'octagon'):
            self.width = outer_diameter
            self.height = outer_diameter
        else:
            # Hexagon
            self.width = 0.5 * math.sqrt(3.) * outer_diameter
            self.height = outer_diameter
        self._to_convert = ['position', 'width', 'height', 'inner_diameter', 'outer_diameter']

    @property
    def lower_left(self):
        return (self.position[0] - (self.width / 2.),
                self.position[1] - (self.height / 2.))

    @property
    def upper_right(self):
        return (self.position[0] + (self.width / 2.),
                self.position[1] + (self.height / 2.))

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))


class SquareRoundDonut(Primitive):
    """ A Square with a circular cutout in the center
    """
    def __init__(self, position, inner_diameter, outer_diameter, **kwargs):
        super(SquareRoundDonut, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        if inner_diameter >= outer_diameter:
            raise ValueError('Outer diameter must be larger than inner diameter.')
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        self._to_convert = ['position', 'inner_diameter', 'outer_diameter']

    @property
    def lower_left(self):
        return tuple([c - self.outer_diameter / 2. for c in self.position])

    @property
    def upper_right(self):
        return tuple([c + self.outer_diameter / 2. for c in self.position])

    @property
    def bounding_box(self):
        min_x = self.lower_left[0]
        max_x = self.upper_right[0]
        min_y = self.lower_left[1]
        max_y = self.upper_right[1]
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))


class Drill(Primitive):
    """ A drill hole
    """
    def __init__(self, position, diameter, **kwargs):
        super(Drill, self).__init__('dark', **kwargs)
        validate_coordinates(position)
        self.position = position
        self.diameter = diameter
        self._to_convert = ['position', 'diameter']

    @property
    def radius(self):
        return self.diameter / 2.

    @property
    def bounding_box(self):
        min_x = self.position[0] - self.radius
        max_x = self.position[0] + self.radius
        min_y = self.position[1] - self.radius
        max_y = self.position[1] + self.radius
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

class TestRecord(Primitive):
    """ Netlist Test record
    """
    def __init__(self, position, net_name, layer, **kwargs):
        super(TestRecord, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.net_name = net_name
        self.layer = layer

