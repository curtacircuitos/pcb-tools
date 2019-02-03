#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2016 Hamilton Kibbe <ham@hamiltonkib.be>

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
from operator import add
from itertools import combinations
from .utils import validate_coordinates, inch, metric, convex_hull
from .utils import rotate_point, nearly_equal




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

    units : string
        Units in which primitive was defined. 'inch' or 'metric'

    net_name : string
        Name of the electrical net the primitive belongs to
    """

    def __init__(self, level_polarity='dark', rotation=0, units=None, net_name=None):
        self.level_polarity = level_polarity
        self.net_name = net_name
        self._to_convert = list()
        self._memoized = list()
        self._units = units
        self._rotation = rotation
        self._cos_theta = math.cos(math.radians(rotation))
        self._sin_theta = math.sin(math.radians(rotation))
        self._bounding_box = None
        self._vertices = None
        self._segments = None

    @property
    def flashed(self):
        '''Is this a flashed primitive'''
        raise NotImplementedError('Is flashed must be '
                                  'implemented in subclass')

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, value):
        self._changed()
        self._units = value

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._changed()
        self._rotation = value
        self._cos_theta = math.cos(math.radians(value))
        self._sin_theta = math.sin(math.radians(value))

    @property
    def vertices(self):
        return None

    @property
    def segments(self):
        if self._segments is None:
            if self.vertices is not None and len(self.vertices):
                self._segments = [segment for segment in
                                  combinations(self.vertices, 2)]
        return self._segments

    @property
    def bounding_box(self):
        """ Calculate axis-aligned bounding box

        will be helpful for sweep & prune during DRC clearance checks.

        Return ((min x, max x), (min y, max y))
        """
        raise NotImplementedError('Bounding box calculation must be '
                                  'implemented in subclass')

    @property
    def bounding_box_no_aperture(self):
        """ Calculate bouxing box without considering the aperture

        for most objects, this is the same as the bounding_box, but is different for
        Lines and Arcs (which are not flashed)

        Return ((min x, max x), (min y, max y))
        """
        return self.bounding_box

    def to_inch(self):
        """ Convert primitive units to inches.
        """
        if self.units == 'metric':
            self.units = 'inch'
            for attr, value in [(attr, getattr(self, attr))
                                for attr in self._to_convert]:
                if hasattr(value, 'to_inch'):
                    value.to_inch()
                else:
                    try:
                        if len(value) > 1:
                            if hasattr(value[0], 'to_inch'):
                                for v in value:
                                    v.to_inch()
                            elif isinstance(value[0], tuple):
                                setattr(self, attr,
                                        [tuple(map(inch, point))
                                         for point in value])
                            else:
                                setattr(self, attr, tuple(map(inch, value)))
                    except:
                        if value is not None:
                            setattr(self, attr, inch(value))

    def to_metric(self):
        """ Convert primitive units to metric.
        """
        if self.units == 'inch':
            self.units = 'metric'
            for attr, value in [(attr, getattr(self, attr))
                                for attr in self._to_convert]:
                if hasattr(value, 'to_metric'):
                    value.to_metric()
                else:
                    try:
                        if len(value) > 1:
                            if hasattr(value[0], 'to_metric'):
                                for v in value:
                                    v.to_metric()
                            elif isinstance(value[0], tuple):
                                setattr(self, attr,
                                        [tuple(map(metric, point))
                                         for point in value])
                            else:
                                setattr(self, attr, tuple(map(metric, value)))
                    except:
                        if value is not None:
                            setattr(self, attr, metric(value))

    def offset(self, x_offset=0, y_offset=0):
        """ Move the primitive by the specified x and y offset amount.

        values are specified in the primitive's native units
        """
        if hasattr(self, 'position'):
            self._changed()
            self.position = tuple([coord + offset for coord, offset
                                   in zip(self.position,
                                          (x_offset, y_offset))])

    def to_statement(self):
        pass

    def _changed(self):
        """ Clear memoized properties.

        Forces a recalculation next time any memoized propery is queried.
        This must be called from a subclass every time a parameter that affects
        a memoized property is changed. The easiest way to do this is to call
        _changed() from property.setter methods.
        """
        self._bounding_box = None
        self._vertices = None
        self._segments = None
        for attr in self._memoized:
            setattr(self, attr, None)

class Line(Primitive):
    """
    """

    def __init__(self, start, end, aperture, level_polarity=None, **kwargs):
        super(Line, self).__init__(**kwargs)
        self.level_polarity = level_polarity
        self._start = start
        self._end = end
        self.aperture = aperture
        self._to_convert = ['start', 'end', 'aperture']

    @property
    def flashed(self):
        return False

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._changed()
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._changed()
        self._end = value

    @property
    def angle(self):
        delta_x, delta_y = tuple(
            [end - start for end, start in zip(self.end, self.start)])
        angle = math.atan2(delta_y, delta_x)
        return angle

    @property
    def bounding_box(self):
        if self._bounding_box is None:
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
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    @property
    def bounding_box_no_aperture(self):
        '''Gets the bounding box without the aperture'''
        min_x = min(self.start[0], self.end[0])
        max_x = max(self.start[0], self.end[0])
        min_y = min(self.start[1], self.end[1])
        max_y = max(self.start[1], self.end[1])
        return ((min_x, max_x), (min_y, max_y))

    @property
    def vertices(self):
        if self._vertices is None:
            start = self.start
            end = self.end
            if isinstance(self.aperture, Rectangle):
                width = self.aperture.width
                height = self.aperture.height

                # Find all the corners of the start and end position
                start_ll = (start[0] - (width / 2.), start[1] - (height / 2.))
                start_lr = (start[0] + (width / 2.), start[1] - (height / 2.))
                start_ul = (start[0] - (width / 2.), start[1] + (height / 2.))
                start_ur = (start[0] + (width / 2.), start[1] + (height / 2.))
                end_ll = (end[0] - (width / 2.), end[1] - (height / 2.))
                end_lr = (end[0] + (width / 2.), end[1] - (height / 2.))
                end_ul = (end[0] - (width / 2.), end[1] + (height / 2.))
                end_ur = (end[0] + (width / 2.), end[1] + (height / 2.))

                # The line is defined by the convex hull of the points
                self._vertices = convex_hull((start_ll, start_lr, start_ul, start_ur, end_ll, end_lr, end_ul, end_ur))
            elif isinstance(self.aperture, Polygon):
                points = [map(add, point, vertex)
                          for vertex in self.aperture.vertices
                          for point in (start, end)]
                self._vertices = convex_hull(points)
        return self._vertices

    def offset(self, x_offset=0, y_offset=0):
        self._changed()
        self.start = tuple([coord + offset for coord, offset
                            in zip(self.start, (x_offset, y_offset))])
        self.end = tuple([coord + offset for coord, offset
                          in zip(self.end, (x_offset, y_offset))])

    def equivalent(self, other, offset):

        if not isinstance(other, Line):
            return False

        equiv_start = tuple(map(add, other.start, offset))
        equiv_end = tuple(map(add, other.end, offset))


        return nearly_equal(self.start, equiv_start) and nearly_equal(self.end, equiv_end)

    def __str__(self):
        return "<Line {} to {}>".format(self.start, self.end)

    def __repr__(self):
        return str(self)

class Arc(Primitive):
    """
    """

    def __init__(self, start, end, center, direction, aperture, quadrant_mode,
            level_polarity=None, **kwargs):
        super(Arc, self).__init__(**kwargs)
        self.level_polarity = level_polarity
        self._start = start
        self._end = end
        self._center = center
        self.direction = direction
        self.aperture = aperture
        self._quadrant_mode = quadrant_mode
        self._to_convert = ['start', 'end', 'center', 'aperture']

    @property
    def flashed(self):
        return False

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._changed()
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._changed()
        self._end = value

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value):
        self._changed()
        self._center = value

    @property
    def quadrant_mode(self):
        return self._quadrant_mode

    @quadrant_mode.setter
    def quadrant_mode(self, quadrant_mode):
        self._changed()
        self._quadrant_mode = quadrant_mode

    @property
    def radius(self):
        dy, dx = tuple([start - center for start, center
                        in zip(self.start, self.center)])
        return math.sqrt(dy ** 2 + dx ** 2)

    @property
    def start_angle(self):
        dx, dy = tuple([start - center for start, center
                        in zip(self.start, self.center)])
        return math.atan2(dy, dx)

    @property
    def end_angle(self):
        dx, dy = tuple([end - center for end, center
                        in zip(self.end, self.center)])
        return math.atan2(dy, dx)

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
        if self._bounding_box is None:
            two_pi = 2 * math.pi
            theta0 = (self.start_angle + two_pi) % two_pi
            theta1 = (self.end_angle + two_pi) % two_pi
            points = [self.start, self.end]
            if self.quadrant_mode == 'multi-quadrant':
                if self.direction == 'counterclockwise':
                    # Passes through 0 degrees
                    if theta0 >= theta1:
                        points.append((self.center[0] + self.radius, self.center[1]))
                    # Passes through 90 degrees
                    if (((theta0 <= math.pi / 2.) and ((theta1 >= math.pi / 2.) or (theta1 <= theta0)))
                        or ((theta1 > math.pi / 2.) and (theta1 <= theta0))):
                        points.append((self.center[0], self.center[1] + self.radius))
                    # Passes through 180 degrees
                    if ((theta0 <= math.pi and (theta1 >= math.pi or theta1 <= theta0))
                        or ((theta1 > math.pi) and (theta1 <= theta0))):
                        points.append((self.center[0] - self.radius, self.center[1]))
                    # Passes through 270 degrees
                    if (theta0 <= math.pi * 1.5 and (theta1 >= math.pi * 1.5 or theta1 <= theta0)
                        or ((theta1 > math.pi * 1.5) and (theta1 <= theta0))):
                        points.append((self.center[0], self.center[1] - self.radius))
                else:
                    # Passes through 0 degrees
                    if theta1 >= theta0:
                        points.append((self.center[0] + self.radius, self.center[1]))
                    # Passes through 90 degrees
                    if (((theta1 <= math.pi / 2.) and (theta0 >= math.pi / 2. or theta0 <= theta1))
                        or ((theta0 > math.pi / 2.) and (theta0 <= theta1))):
                        points.append((self.center[0], self.center[1] + self.radius))
                    # Passes through 180 degrees
                    if (((theta1 <= math.pi) and (theta0 >= math.pi or theta0 <= theta1))
                        or ((theta0 > math.pi) and (theta0 <= theta1))):
                        points.append((self.center[0] - self.radius, self.center[1]))
                    # Passes through 270 degrees
                    if (((theta1 <= math.pi * 1.5) and (theta0 >= math.pi * 1.5 or theta0 <= theta1))
                        or ((theta0 > math.pi * 1.5) and (theta0 <= theta1))):
                        points.append((self.center[0], self.center[1] - self.radius))
            x, y = zip(*points)
            if hasattr(self.aperture, 'radius'):
                min_x = min(x) - self.aperture.radius
                max_x = max(x) + self.aperture.radius
                min_y = min(y) - self.aperture.radius
                max_y = max(y) + self.aperture.radius
            else:
                min_x = min(x) - self.aperture.width
                max_x = max(x) + self.aperture.width
                min_y = min(y) - self.aperture.height
                max_y = max(y) + self.aperture.height

            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    @property
    def bounding_box_no_aperture(self):
        '''Gets the bounding box without considering the aperture'''
        two_pi = 2 * math.pi
        theta0 = (self.start_angle + two_pi) % two_pi
        theta1 = (self.end_angle + two_pi) % two_pi
        points = [self.start, self.end]
        if self.quadrant_mode == 'multi-quadrant':
            if self.direction == 'counterclockwise':
                # Passes through 0 degrees
                if theta0 >= theta1:
                    points.append((self.center[0] + self.radius, self.center[1]))
                # Passes through 90 degrees
                if (((theta0 <= math.pi / 2.) and (
                    (theta1 >= math.pi / 2.) or (theta1 <= theta0)))
                    or ((theta1 > math.pi / 2.) and (theta1 <= theta0))):
                    points.append((self.center[0], self.center[1] + self.radius))
                # Passes through 180 degrees
                if ((theta0 <= math.pi and (theta1 >= math.pi or theta1 <= theta0))
                    or ((theta1 > math.pi) and (theta1 <= theta0))):
                    points.append((self.center[0] - self.radius, self.center[1]))
                # Passes through 270 degrees
                if (theta0 <= math.pi * 1.5 and (
                        theta1 >= math.pi * 1.5 or theta1 <= theta0)
                    or ((theta1 > math.pi * 1.5) and (theta1 <= theta0))):
                    points.append((self.center[0], self.center[1] - self.radius))
            else:
                # Passes through 0 degrees
                if theta1 >= theta0:
                    points.append((self.center[0] + self.radius, self.center[1]))
                # Passes through 90 degrees
                if (((theta1 <= math.pi / 2.) and (
                        theta0 >= math.pi / 2. or theta0 <= theta1))
                    or ((theta0 > math.pi / 2.) and (theta0 <= theta1))):
                    points.append((self.center[0], self.center[1] + self.radius))
                # Passes through 180 degrees
                if (((theta1 <= math.pi) and (theta0 >= math.pi or theta0 <= theta1))
                    or ((theta0 > math.pi) and (theta0 <= theta1))):
                    points.append((self.center[0] - self.radius, self.center[1]))
                # Passes through 270 degrees
                if (((theta1 <= math.pi * 1.5) and (
                        theta0 >= math.pi * 1.5 or theta0 <= theta1))
                    or ((theta0 > math.pi * 1.5) and (theta0 <= theta1))):
                    points.append((self.center[0], self.center[1] - self.radius))
        x, y = zip(*points)

        min_x = min(x)
        max_x = max(x)
        min_y = min(y)
        max_y = max(y)
        return ((min_x, max_x), (min_y, max_y))

    def offset(self, x_offset=0, y_offset=0):
        self._changed()
        self.start = tuple(map(add, self.start, (x_offset, y_offset)))
        self.end = tuple(map(add, self.end, (x_offset, y_offset)))
        self.center = tuple(map(add, self.center, (x_offset, y_offset)))


class Circle(Primitive):
    """
    """

    def __init__(self, position, diameter, hole_diameter=None,
                 hole_width=0, hole_height=0, **kwargs):
        super(Circle, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._diameter = diameter
        self.hole_diameter = hole_diameter
        self.hole_width = hole_width
        self.hole_height = hole_height
        self._to_convert = ['position', 'diameter', 'hole_diameter', 'hole_width', 'hole_height']

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, value):
        self._changed()
        self._diameter = value

    @property
    def radius(self):
        return self.diameter / 2.

    @property
    def hole_radius(self):
        if self.hole_diameter != None:
            return self.hole_diameter / 2.
        return None

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            min_x = self.position[0] - self.radius
            max_x = self.position[0] + self.radius
            min_y = self.position[1] - self.radius
            max_y = self.position[1] + self.radius
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    def equivalent(self, other, offset):
        '''Is this the same as the other circle, ignoring the offiset?'''

        if not isinstance(other, Circle):
            return False

        if self.diameter != other.diameter or self.hole_diameter != other.hole_diameter:
            return False

        equiv_position = tuple(map(add, other.position, offset))

        return nearly_equal(self.position, equiv_position)


class Ellipse(Primitive):
    """
    """
    def __init__(self, position, width, height, **kwargs):
        super(Ellipse, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._width = width
        self._height = height
        self._to_convert = ['position', 'width', 'height']

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._changed()
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._changed()
        self._height = value

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            min_x = self.position[0] - (self.axis_aligned_width / 2.0)
            max_x = self.position[0] + (self.axis_aligned_width / 2.0)
            min_y = self.position[1] - (self.axis_aligned_height / 2.0)
            max_y = self.position[1] + (self.axis_aligned_height / 2.0)
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    @property
    def axis_aligned_width(self):
        ux = (self.width / 2.) * math.cos(math.radians(self.rotation))
        vx = (self.height / 2.) * \
            math.cos(math.radians(self.rotation) + (math.pi / 2.))
        return 2 * math.sqrt((ux * ux) + (vx * vx))

    @property
    def axis_aligned_height(self):
        uy = (self.width / 2.) * math.sin(math.radians(self.rotation))
        vy = (self.height / 2.) * \
            math.sin(math.radians(self.rotation) + (math.pi / 2.))
        return 2 * math.sqrt((uy * uy) + (vy * vy))


class Rectangle(Primitive):
    """
    When rotated, the rotation is about the center point.

    Only aperture macro generated Rectangle objects can be rotated. If you aren't in a AMGroup,
    then you don't need to worry about rotation
    """

    def __init__(self, position, width, height, hole_diameter=0,
                 hole_width=0, hole_height=0, **kwargs):
        super(Rectangle, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._width = width
        self._height = height
        self.hole_diameter = hole_diameter
        self.hole_width = hole_width
        self.hole_height = hole_height
        self._to_convert = ['position', 'width', 'height', 'hole_diameter',
                            'hole_width', 'hole_height']
        # TODO These are probably wrong when rotated
        self._lower_left = None
        self._upper_right = None

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._changed()
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._changed()
        self._height = value

    @property
    def hole_radius(self):
        """The radius of the hole. If there is no hole, returns None"""
        if self.hole_diameter != None:
            return self.hole_diameter / 2.
        return None

    @property
    def upper_right(self):
        return (self.position[0] + (self.axis_aligned_width / 2.),
                self.position[1] + (self.axis_aligned_height / 2.))

    @property
    def lower_left(self):
        return (self.position[0] - (self.axis_aligned_width / 2.),
                self.position[1] - (self.axis_aligned_height / 2.))

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            ll = (self.position[0] - (self.axis_aligned_width / 2.),
                  self.position[1] - (self.axis_aligned_height / 2.))
            ur = (self.position[0] + (self.axis_aligned_width / 2.),
                  self.position[1] + (self.axis_aligned_height / 2.))
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box

    @property
    def vertices(self):
        if self._vertices is None:
            delta_w = self.width / 2.
            delta_h = self.height / 2.
            ll = ((self.position[0] - delta_w), (self.position[1] - delta_h))
            ul = ((self.position[0] - delta_w), (self.position[1] + delta_h))
            ur = ((self.position[0] + delta_w), (self.position[1] + delta_h))
            lr = ((self.position[0] + delta_w), (self.position[1] - delta_h))
            self._vertices = [((x * self._cos_theta - y * self._sin_theta),
                               (x * self._sin_theta + y * self._cos_theta))
                              for x, y in [ll, ul, ur, lr]]
        return self._vertices

    @property
    def axis_aligned_width(self):
        return (self._cos_theta * self.width + self._sin_theta * self.height)

    @property
    def axis_aligned_height(self):
        return (self._cos_theta * self.height + self._sin_theta * self.width)

    def equivalent(self, other, offset):
        """Is this the same as the other rect, ignoring the offset?"""

        if not isinstance(other, Rectangle):
            return False

        if self.width != other.width or self.height != other.height or self.rotation != other.rotation or self.hole_diameter != other.hole_diameter:
            return False

        equiv_position = tuple(map(add, other.position, offset))

        return nearly_equal(self.position, equiv_position)

    def __str__(self):
        return "<Rectangle W {} H {} R {}>".format(self.width, self.height, self.rotation * 180/math.pi)

    def __repr__(self):
        return self.__str__()


class Diamond(Primitive):
    """
    """

    def __init__(self, position, width, height, **kwargs):
        super(Diamond, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._width = width
        self._height = height
        self._to_convert = ['position', 'width', 'height']

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._changed()
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._changed()
        self._height = value

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            ll = (self.position[0] - (self.axis_aligned_width / 2.),
                  self.position[1] - (self.axis_aligned_height / 2.))
            ur = (self.position[0] + (self.axis_aligned_width / 2.),
                  self.position[1] + (self.axis_aligned_height / 2.))
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box

    @property
    def vertices(self):
        if self._vertices is None:
            delta_w = self.width / 2.
            delta_h = self.height / 2.
            top = (self.position[0], (self.position[1] + delta_h))
            right = ((self.position[0] + delta_w), self.position[1])
            bottom = (self.position[0], (self.position[1] - delta_h))
            left = ((self.position[0] - delta_w), self.position[1])
            self._vertices = [(((x * self._cos_theta) - (y * self._sin_theta)),
                               ((x * self._sin_theta) + (y * self._cos_theta)))
                              for x, y in [top, right, bottom, left]]
        return self._vertices

    @property
    def axis_aligned_width(self):
        return (self._cos_theta * self.width + self._sin_theta * self.height)

    @property
    def axis_aligned_height(self):
        return (self._cos_theta * self.height + self._sin_theta * self.width)


class ChamferRectangle(Primitive):
    """
    """
    def __init__(self, position, width, height, chamfer, corners=None, **kwargs):
        super(ChamferRectangle, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._width = width
        self._height = height
        self._chamfer = chamfer
        self._corners = corners if corners is not None else [True] * 4
        self._to_convert = ['position', 'width', 'height', 'chamfer']

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._changed()
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._changed()
        self._height = value

    @property
    def chamfer(self):
        return self._chamfer

    @chamfer.setter
    def chamfer(self, value):
        self._changed()
        self._chamfer = value

    @property
    def corners(self):
        return self._corners

    @corners.setter
    def corners(self, value):
        self._changed()
        self._corners = value

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            ll = (self.position[0] - (self.axis_aligned_width / 2.),
                  self.position[1] - (self.axis_aligned_height / 2.))
            ur = (self.position[0] + (self.axis_aligned_width / 2.),
                  self.position[1] + (self.axis_aligned_height / 2.))
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box

    @property
    def vertices(self):
        if self._vertices is None:
            vertices = []
            delta_w = self.width / 2.
            delta_h = self.height / 2.
            # order is UR, UL, LL, LR
            rect_corners = [
                ((self.position[0] + delta_w), (self.position[1] + delta_h)),
                ((self.position[0] - delta_w), (self.position[1] + delta_h)),
                ((self.position[0] - delta_w), (self.position[1] - delta_h)),
                ((self.position[0] + delta_w), (self.position[1] - delta_h))
            ]
            for idx, params in enumerate(zip(rect_corners, self.corners)):
                corner, chamfered = params
                x, y = corner
                if chamfered:
                    if idx == 0:
                        vertices.append((x - self.chamfer, y))
                        vertices.append((x, y - self.chamfer))
                    elif idx == 1:
                        vertices.append((x + self.chamfer, y))
                        vertices.append((x, y - self.chamfer))
                    elif idx == 2:
                        vertices.append((x + self.chamfer, y))
                        vertices.append((x, y + self.chamfer))
                    elif idx == 3:
                        vertices.append((x - self.chamfer, y))
                        vertices.append((x, y + self.chamfer))
                else:
                    vertices.append(corner)
            self._vertices = [((x * self._cos_theta - y * self._sin_theta),
                               (x * self._sin_theta + y * self._cos_theta))
                              for x, y in vertices]
        return self._vertices

    @property
    def axis_aligned_width(self):
        return (self._cos_theta * self.width +
                self._sin_theta * self.height)

    @property
    def axis_aligned_height(self):
        return (self._cos_theta * self.height +
                self._sin_theta * self.width)


class RoundRectangle(Primitive):
    """
    """

    def __init__(self, position, width, height, radius, corners, **kwargs):
        super(RoundRectangle, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._width = width
        self._height = height
        self._radius = radius
        self._corners = corners
        self._to_convert = ['position', 'width', 'height', 'radius']

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._changed()
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._changed()
        self._height = value

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._changed()
        self._radius = value

    @property
    def corners(self):
        return self._corners

    @corners.setter
    def corners(self, value):
        self._changed()
        self._corners = value

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            ll = (self.position[0] - (self.axis_aligned_width / 2.),
                  self.position[1] - (self.axis_aligned_height / 2.))
            ur = (self.position[0] + (self.axis_aligned_width / 2.),
                  self.position[1] + (self.axis_aligned_height / 2.))
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box

    @property
    def axis_aligned_width(self):
        return (self._cos_theta * self.width +
                self._sin_theta * self.height)

    @property
    def axis_aligned_height(self):
        return (self._cos_theta * self.height +
                self._sin_theta * self.width)


class Obround(Primitive):
    """
    """

    def __init__(self, position, width, height, hole_diameter=0,
                 hole_width=0,hole_height=0, **kwargs):
        super(Obround, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self._width = width
        self._height = height
        self.hole_diameter = hole_diameter
        self.hole_width = hole_width
        self.hole_height = hole_height
        self._to_convert = ['position', 'width', 'height', 'hole_diameter',
                            'hole_width', 'hole_height' ]

    @property
    def flashed(self):
        return True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._changed()
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._changed()
        self._height = value

    @property
    def hole_radius(self):
        """The radius of the hole. If there is no hole, returns None"""
        if self.hole_diameter != None:
            return self.hole_diameter / 2.

        return None

    @property
    def orientation(self):
        return 'vertical' if self.height > self.width else 'horizontal'

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            ll = (self.position[0] - (self.axis_aligned_width / 2.),
                  self.position[1] - (self.axis_aligned_height / 2.))
            ur = (self.position[0] + (self.axis_aligned_width / 2.),
                  self.position[1] + (self.axis_aligned_height / 2.))
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box

    @property
    def subshapes(self):
        if self.orientation == 'vertical':
            circle1 = Circle((self.position[0], self.position[1] +
                              (self.height - self.width) / 2.), self.width)
            circle2 = Circle((self.position[0], self.position[1] -
                              (self.height - self.width) / 2.), self.width)
            rect = Rectangle(self.position, self.width,
                             (self.height - self.width))
        else:
            circle1 = Circle((self.position[0]
                              - (self.height - self.width) / 2.,
                              self.position[1]), self.height)
            circle2 = Circle((self.position[0]
                              + (self.height - self.width) / 2.,
                              self.position[1]), self.height)
            rect = Rectangle(self.position, (self.width - self.height),
                             self.height)
        return {'circle1': circle1, 'circle2': circle2, 'rectangle': rect}

    @property
    def axis_aligned_width(self):
        return (self._cos_theta * self.width +
                self._sin_theta * self.height)

    @property
    def axis_aligned_height(self):
        return (self._cos_theta * self.height +
                self._sin_theta * self.width)


class Polygon(Primitive):
    """
    Polygon flash defined by a set number of sides.
    """
    def __init__(self, position, sides, radius, hole_diameter=0,
                 hole_width=0, hole_height=0, **kwargs):
        super(Polygon, self).__init__(**kwargs)
        validate_coordinates(position)
        self._position = position
        self.sides = sides
        self._radius = radius
        self.hole_diameter = hole_diameter
        self.hole_width = hole_width
        self.hole_height = hole_height
        self._to_convert = ['position', 'radius', 'hole_diameter',
                            'hole_width', 'hole_height']

    @property
    def flashed(self):
        return True

    @property
    def diameter(self):
        return self.radius * 2

    @property
    def hole_radius(self):
        if self.hole_diameter != None:
            return self.hole_diameter / 2.
        return None

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._changed()
        self._radius = value

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            min_x = self.position[0] - self.radius
            max_x = self.position[0] + self.radius
            min_y = self.position[1] - self.radius
            max_y = self.position[1] + self.radius
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    def offset(self, x_offset=0, y_offset=0):
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    @property
    def vertices(self):

        offset = self.rotation
        delta_angle = 360.0 / self.sides

        points = []
        for i in range(self.sides):
            points.append(
                rotate_point((self.position[0] + self.radius, self.position[1]), offset + delta_angle * i, self.position))
        return points


    def equivalent(self, other, offset):
        """
        Is this the outline the same as the other, ignoring the position offset?
        """

        # Quick check if it even makes sense to compare them
        if type(self) != type(other) or self.sides != other.sides or self.radius != other.radius:
            return False

        equiv_pos = tuple(map(add, other.position, offset))

        return nearly_equal(self.position, equiv_pos)


class AMGroup(Primitive):
    """
    """
    def __init__(self, amprimitives, stmt = None, **kwargs):
        """

        stmt : The original statment that generated this, since it is really hard to re-generate from primitives
        """
        super(AMGroup, self).__init__(**kwargs)

        self.primitives = []
        for amprim in amprimitives:
            prim = amprim.to_primitive(self.units)
            if isinstance(prim, list):
                for p in prim:
                    self.primitives.append(p)
            elif prim:
                self.primitives.append(prim)
        self._position = None
        self._to_convert = ['_position', 'primitives']
        self.stmt = stmt

    def to_inch(self):
        if self.units == 'metric':
            super(AMGroup, self).to_inch()

            # If we also have a stmt, convert that too
            if self.stmt:
                self.stmt.to_inch()


    def to_metric(self):
        if self.units == 'inch':
            super(AMGroup, self).to_metric()

            # If we also have a stmt, convert that too
            if self.stmt:
                self.stmt.to_metric()

    @property
    def flashed(self):
        return True

    @property
    def bounding_box(self):
        # TODO Make this cached like other items
        xlims, ylims = zip(*[p.bounding_box for p in self.primitives])
        minx, maxx = zip(*xlims)
        miny, maxy = zip(*ylims)
        min_x = min(minx)
        max_x = max(maxx)
        min_y = min(miny)
        max_y = max(maxy)
        return ((min_x, max_x), (min_y, max_y))

    @property
    def position(self):
        return self._position

    def offset(self, x_offset=0, y_offset=0):
        self._position = tuple(map(add, self._position, (x_offset, y_offset)))

        for primitive in self.primitives:
            primitive.offset(x_offset, y_offset)

    @position.setter
    def position(self, new_pos):
        '''
        Sets the position of the AMGroup.
        This offset all of the objects by the specified distance.
        '''

        if self._position:
            dx = new_pos[0] - self._position[0]
            dy = new_pos[1] - self._position[1]
        else:
            dx = new_pos[0]
            dy = new_pos[1]

        for primitive in self.primitives:
            primitive.offset(dx, dy)

        self._position = new_pos

    def equivalent(self, other, offset):
        '''
        Is this the macro group the same as the other, ignoring the position offset?
        '''

        if len(self.primitives) != len(other.primitives):
            return False

        # We know they have the same number of primitives, so now check them all
        for i in range(0, len(self.primitives)):
            if not self.primitives[i].equivalent(other.primitives[i], offset):
                return False

        # If we didn't find any differences, then they are the same
        return True

class Outline(Primitive):
    """
    Outlines only exist as the rendering for a apeture macro outline.
    They don't exist outside of AMGroup objects
    """

    def __init__(self, primitives, **kwargs):
        super(Outline, self).__init__(**kwargs)
        self.primitives = primitives
        self._to_convert = ['primitives']

        if self.primitives[0].start != self.primitives[-1].end:
            raise ValueError('Outline must be closed')

    @property
    def flashed(self):
        return True

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            xlims, ylims = zip(*[p.bounding_box for p in self.primitives])
            minx, maxx = zip(*xlims)
            miny, maxy = zip(*ylims)
            min_x = min(minx)
            max_x = max(maxx)
            min_y = min(miny)
            max_y = max(maxy)
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    def offset(self, x_offset=0, y_offset=0):
        self._changed()
        for p in self.primitives:
            p.offset(x_offset, y_offset)

    @property
    def vertices(self):
        if self._vertices is None:
            theta = math.radians(360/self.sides)
            vertices = [(self.position[0] + (math.cos(theta * side) * self.radius),
                         self.position[1] + (math.sin(theta * side) * self.radius))
                        for side in range(self.sides)]
            self._vertices = [(((x * self._cos_theta) - (y * self._sin_theta)),
                               ((x * self._sin_theta) + (y * self._cos_theta)))
                              for x, y in vertices]
        return self._vertices

    @property
    def width(self):
        bounding_box = self.bounding_box()
        return bounding_box[0][1] - bounding_box[0][0]

    def equivalent(self, other, offset):
        '''
        Is this the outline the same as the other, ignoring the position offset?
        '''

        # Quick check if it even makes sense to compare them
        if type(self) != type(other) or len(self.primitives) != len(other.primitives):
            return False

        for i in range(0, len(self.primitives)):
            if not self.primitives[i].equivalent(other.primitives[i], offset):
                return False

        return True

class Region(Primitive):
    """
    """

    def __init__(self, primitives, **kwargs):
        super(Region, self).__init__(**kwargs)
        self.primitives = primitives
        self._to_convert = ['primitives']

    @property
    def flashed(self):
        return False

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            xlims, ylims = zip(*[p.bounding_box_no_aperture for p in self.primitives])
            minx, maxx = zip(*xlims)
            miny, maxy = zip(*ylims)
            min_x = min(minx)
            max_x = max(maxx)
            min_y = min(miny)
            max_y = max(maxy)
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    def offset(self, x_offset=0, y_offset=0):
        self._changed()
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

        # TODO This does not reset bounding box correctly

    @property
    def flashed(self):
        return True

    @property
    def radius(self):
        return self.diameter / 2.

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            min_x = self.position[0] - self.radius
            max_x = self.position[0] + self.radius
            min_y = self.position[1] - self.radius
            max_y = self.position[1] + self.radius
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box


class SquareButterfly(Primitive):
    """ A square with two diagonally-opposite quadrants removed
    """

    def __init__(self, position, side, **kwargs):
        super(SquareButterfly, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.side = side
        self._to_convert = ['position', 'side']

        # TODO This does not reset bounding box correctly

    @property
    def flashed(self):
        return True

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            min_x = self.position[0] - (self.side / 2.)
            max_x = self.position[0] + (self.side / 2.)
            min_y = self.position[1] - (self.side / 2.)
            max_y = self.position[1] + (self.side / 2.)
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box


class Donut(Primitive):
    """ A Shape with an identical concentric shape removed from its center
    """

    def __init__(self, position, shape, inner_diameter,
                 outer_diameter, **kwargs):
        super(Donut, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        if shape not in ('round', 'square', 'hexagon', 'octagon'):
            raise ValueError(
                'Valid shapes are round, square, hexagon or octagon')
        self.shape = shape
        if inner_diameter >= outer_diameter:
            raise ValueError(
                'Outer diameter must be larger than inner diameter.')
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        if self.shape in ('round', 'square', 'octagon'):
            self.width = outer_diameter
            self.height = outer_diameter
        else:
            # Hexagon
            self.width = 0.5 * math.sqrt(3.) * outer_diameter
            self.height = outer_diameter

        self._to_convert = ['position', 'width',
                            'height', 'inner_diameter', 'outer_diameter']

        # TODO This does not reset bounding box correctly

    @property
    def flashed(self):
        return True

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
        if self._bounding_box is None:
            ll = (self.position[0] - (self.width / 2.),
                  self.position[1] - (self.height / 2.))
            ur = (self.position[0] + (self.width / 2.),
                  self.position[1] + (self.height / 2.))
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box


class SquareRoundDonut(Primitive):
    """ A Square with a circular cutout in the center
    """

    def __init__(self, position, inner_diameter, outer_diameter, **kwargs):
        super(SquareRoundDonut, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        if inner_diameter >= outer_diameter:
            raise ValueError(
                'Outer diameter must be larger than inner diameter.')
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        self._to_convert = ['position', 'inner_diameter', 'outer_diameter']

    @property
    def flashed(self):
        return True

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            ll = tuple([c - self.outer_diameter / 2. for c in self.position])
            ur = tuple([c + self.outer_diameter / 2. for c in self.position])
            self._bounding_box = ((ll[0], ur[0]), (ll[1], ur[1]))
        return self._bounding_box


class Drill(Primitive):
    """ A drill hole
    """
    def __init__(self, position, diameter, **kwargs):
        super(Drill, self).__init__('dark', **kwargs)
        validate_coordinates(position)
        self._position = position
        self._diameter = diameter
        self._to_convert = ['position', 'diameter']

    @property
    def flashed(self):
        return False

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._changed()
        self._position = value

    @property
    def diameter(self):
        return self._diameter

    @diameter.setter
    def diameter(self, value):
        self._changed()
        self._diameter = value

    @property
    def radius(self):
        return self.diameter / 2.

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            min_x = self.position[0] - self.radius
            max_x = self.position[0] + self.radius
            min_y = self.position[1] - self.radius
            max_y = self.position[1] + self.radius
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    def offset(self, x_offset=0, y_offset=0):
        self._changed()
        self.position = tuple(map(add, self.position, (x_offset, y_offset)))

    def __str__(self):
        return '<Drill %f %s (%f, %f)>' % (self.diameter, self.units, self.position[0], self.position[1])


class Slot(Primitive):
    """ A drilled slot
    """
    def __init__(self, start, end, diameter, **kwargs):
        super(Slot, self).__init__('dark', **kwargs)
        validate_coordinates(start)
        validate_coordinates(end)
        self.start = start
        self.end = end
        self.diameter = diameter
        self._to_convert = ['start', 'end', 'diameter']


    @property
    def flashed(self):
        return False

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            radius = self.diameter / 2.
            min_x = min(self.start[0], self.end[0]) - radius
            max_x = max(self.start[0], self.end[0]) + radius
            min_y = min(self.start[1], self.end[1]) - radius
            max_y = max(self.start[1], self.end[1]) + radius
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    def offset(self, x_offset=0, y_offset=0):
        self.start = tuple(map(add, self.start, (x_offset, y_offset)))
        self.end = tuple(map(add, self.end, (x_offset, y_offset)))


class TestRecord(Primitive):
    """ Netlist Test record
    """

    def __init__(self, position, net_name, layer, **kwargs):
        super(TestRecord, self).__init__(**kwargs)
        validate_coordinates(position)
        self.position = position
        self.net_name = net_name
        self.layer = layer
        self._to_convert = ['position']
