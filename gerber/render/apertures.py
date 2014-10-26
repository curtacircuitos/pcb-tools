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
"""
gerber.render.apertures
============
**Gerber Aperture base classes**

This module provides base classes for gerber apertures. These are used by
the rendering engine to draw the gerber file.
"""
import math

class Aperture(object):
    """ Gerber Aperture base class
    """
    def draw(self, ctx, x, y):
        raise NotImplementedError('The draw method must be implemented \
                                  in an Aperture subclass.')

    def flash(self, ctx, x, y):
        raise NotImplementedError('The flash method must be implemented \
                                  in an Aperture subclass.')

    def _arc_params(self, startx,  starty, x, y, i, j):
        center = (startx + i, starty + j)
        radius = math.sqrt(math.pow(center[0] - x, 2) +
                           math.pow(center[1] - y, 2))
        delta_x0 = startx - center[0]
        delta_y0 = center[1] - starty
        delta_x1 = x - center[0]
        delta_y1 = center[1] - y
        start_angle = math.atan2(delta_y0, delta_x0)
        end_angle = math.atan2(delta_y1, delta_x1)
        return {'center': center, 'radius': radius,
                'start_angle': start_angle, 'end_angle': end_angle}


class Circle(Aperture):
    """ Circular Aperture base class
    """
    def __init__(self, diameter=0.0):
        self.diameter = diameter


class Rect(Aperture):
    """ Rectangular Aperture base class
    """
    def __init__(self, size=(0, 0)):
        self.size = size


class Obround(Aperture):
    """ Obround Aperture base class
    """
    def __init__(self, size=(0, 0)):
        self.size = size


class Polygon(Aperture):
    """ Polygon Aperture base class
    """
    pass
