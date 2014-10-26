#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
#
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
CAM File
============
**AM file classes**

This module provides common base classes for Excellon/Gerber CNC files
"""


class FileSettings(object):
    """ CAM File Settings

    Provides a common representation of gerber/excellon file settings
    """
    def __init__(self, notation='absolute', units='inch',
                 zero_suppression='trailing', format=(2, 5)):
        if notation not in ['absolute', 'incremental']:
            raise ValueError('Notation must be either absolute or incremental')
        self.notation = notation

        if units not in ['inch', 'metric']:
            raise ValueError('Units must be either inch or metric')
        self.units = units

        if zero_suppression not in ['leading', 'trailing']:
            raise ValueError('Zero suppression must be either leading or \
                             trailling')
        self.zero_suppression = zero_suppression

        if len(format) != 2:
            raise ValueError('Format must be a tuple(n=2) of integers')
        self.format = format

    def __getitem__(self, key):
        if key == 'notation':
            return self.notation
        elif key == 'units':
            return self.units
        elif key == 'zero_suppression':
            return self.zero_suppression
        elif key == 'format':
            return self.format
        else:
            raise KeyError()

    def __setitem__(self, key, value):
        if key == 'notation':
            if value not in ['absolute', 'incremental']:
                raise ValueError('Notation must be either \
                                 absolute or incremental')
            self.notation = value
        elif key == 'units':
            if value not in ['inch', 'metric']:
                raise ValueError('Units must be either inch or metric')
            self.units = value
        elif key == 'zero_suppression':
            if value not in ['leading', 'trailing']:
                raise ValueError('Zero suppression must be either leading or \
                                 trailling')
            self.zero_suppression = value
        elif key == 'format':
            if len(value) != 2:
                raise ValueError('Format must be a tuple(n=2) of integers')
            self.format = value

    def __eq__(self, other):
        return (self.notation == other.notation and
                self.units == other.units and
                self.zero_suppression == other.zero_suppression and
                self.format == other.format)



class CamFile(object):
    """ Base class for Gerber/Excellon files.

    Provides a common set of settings parameters.

    Parameters
    ----------
    settings : FileSettings
        The current file configuration.

    primitives : iterable
        List of primitives in the file.

    filename : string
        Name of the file that this CamFile represents.

    layer_name : string
        Name of the PCB layer that the file represents

    Attributes
    ----------
    settings : FileSettings
        File settings as a FileSettings object

    notation : string
        File notation setting. May be either 'absolute' or 'incremental'

    units : string
        File units setting. May be 'inch' or 'metric'

    zero_suppression : string
        File zero-suppression setting. May be either 'leading' or 'trailling'

    format : tuple (<int>, <int>)
        File decimal representation format as a tuple of (integer digits,
        decimal digits)
    """

    def __init__(self, statements=None, settings=None, primitives=None,
                 filename=None, layer_name=None):
        if settings is not None:
            self.notation = settings['notation']
            self.units = settings['units']
            self.zero_suppression = settings['zero_suppression']
            self.format = settings['format']
        else:
            self.notation = 'absolute'
            self.units = 'inch'
            self.zero_suppression = 'trailing'
            self.format = (2, 5)
        self.statements = statements if statements is not None else []
        self.primitives = primitives
        self.filename = filename
        self.layer_name = layer_name

    @property
    def settings(self):
        """ File settings

        Returns
        -------
        settings : FileSettings (dict-like)
            A FileSettings object with the specified configuration.
        """
        return FileSettings(self.notation, self.units, self.zero_suppression,
                            self.format)

    @property
    def bounds(self):
        """ File baundaries
        """
        pass

    def render(self, ctx, filename=None):
        """ Generate image of layer.

        Parameters
        ----------
        ctx : :class:`GerberContext`
            GerberContext subclass used for rendering the image

        filename : string <optional>
            If provided, save the rendered image to `filename`
        """
        ctx.set_bounds(self.bounds)
        for p in self.primitives:
            ctx.render(p)
        if filename is not None:
            ctx.dump(filename)
