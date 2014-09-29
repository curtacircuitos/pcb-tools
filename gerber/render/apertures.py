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


class Aperture(object):
    """ Gerber Aperture base class
    """
    def draw(self, ctx, x, y):
        raise NotImplementedError('The draw method must be implemented in an Aperture subclass.')

    def flash(self, ctx, x, y):
        raise NotImplementedError('The flash method must be implemented in an Aperture subclass.')


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
