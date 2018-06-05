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

    Parameters
    ----------
    notation: string
        notation format. either 'absolute' or 'incremental'

    units : string
        Measurement units. 'inch' or 'metric'

    zero_suppression: string
        'leading' to suppress leading zeros, 'trailing' to suppress trailing zeros.
        This is the convention used in Gerber files.

    format : tuple (int, int)
        Decimal format

    zeros : string
        'leading' to include leading zeros, 'trailing to include trailing zeros.
        This is the convention used in Excellon files

    Notes
    -----
    Either `zeros` or `zero_suppression` should be specified, there is no need to
    specify both. `zero_suppression` will take on the opposite value of `zeros`
    and vice versa
    """

    def __init__(self, notation='absolute', units='inch',
                 zero_suppression=None, format=(2, 5), zeros=None,
                 angle_units='degrees'):
        if notation not in ['absolute', 'incremental']:
            raise ValueError('Notation must be either absolute or incremental')
        self.notation = notation

        if units not in ['inch', 'metric']:
            raise ValueError('Units must be either inch or metric')
        self.units = units

        if zero_suppression is None and zeros is None:
            self.zero_suppression = 'trailing'

        elif zero_suppression == zeros:
            raise ValueError('Zeros and Zero Suppression must be different. \
                             Best practice is to specify only one.')

        elif zero_suppression is not None:
            if zero_suppression not in ['leading', 'trailing']:
                # This is a common problem in Eagle files, so just suppress it
                self.zero_suppression = 'leading'
            else:
                self.zero_suppression = zero_suppression

        elif zeros is not None:
            if zeros not in ['leading', 'trailing']:
                raise ValueError('Zeros must be either leading or trailling')
            self.zeros = zeros

        if len(format) != 2:
            raise ValueError('Format must be a tuple(n=2) of integers')
        self.format = format

        if angle_units not in ('degrees', 'radians'):
            raise ValueError('Angle units may be degrees or radians')
        self.angle_units = angle_units

    @property
    def zero_suppression(self):
        return self._zero_suppression

    @zero_suppression.setter
    def zero_suppression(self, value):
        self._zero_suppression = value
        self._zeros = 'leading' if value == 'trailing' else 'trailing'

    @property
    def zeros(self):
        return self._zeros

    @zeros.setter
    def zeros(self, value):

        self._zeros = value
        self._zero_suppression = 'leading' if value == 'trailing' else 'trailing'

    def __getitem__(self, key):
        if key == 'notation':
            return self.notation
        elif key == 'units':
            return self.units
        elif key == 'zero_suppression':
            return self.zero_suppression
        elif key == 'zeros':
            return self.zeros
        elif key == 'format':
            return self.format
        elif key == 'angle_units':
            return self.angle_units
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

        elif key == 'zeros':
            if value not in ['leading', 'trailing']:
                raise ValueError('Zeros must be either leading or trailling')
            self.zeros = value

        elif key == 'format':
            if len(value) != 2:
                raise ValueError('Format must be a tuple(n=2) of integers')
            self.format = value

        elif key == 'angle_units':
            if value not in ('degrees', 'radians'):
                raise ValueError('Angle units may be degrees or radians')
            self.angle_units = value

        else:
            raise KeyError('%s is not a valid key' % key)

    def __eq__(self, other):
        return (self.notation == other.notation and
                self.units == other.units and
                self.zero_suppression == other.zero_suppression and
                self.format == other.format and
                self.angle_units == other.angle_units)

    def __str__(self):
        return ('<Settings: %s %s %s %s %s>' %
                (self.units, self.notation, self.zero_suppression, self.format, self.angle_units))


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
            self.zeros = settings['zeros']
            self.format = settings['format']
        else:
            self.notation = 'absolute'
            self.units = 'inch'
            self.zero_suppression = 'trailing'
            self.zeros = 'leading'
            self.format = (2, 5)
        self.statements = statements if statements is not None else []
        if primitives is not None:
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
        """ File boundaries
        """
        pass

    @property
    def bounding_box(self):
        pass

    def to_inch(self):
        pass

    def to_metric(self):
        pass

    def render(self, ctx=None, invert=False, filename=None):
        """ Generate image of layer.

        Parameters
        ----------
        ctx : :class:`GerberContext`
            GerberContext subclass used for rendering the image

        filename : string <optional>
            If provided, save the rendered image to `filename`
        """
        if ctx is None:
            from .render import GerberCairoContext
            ctx = GerberCairoContext()
        ctx.set_bounds(self.bounding_box)
        ctx.paint_background()
        ctx.invert = invert
        ctx.new_render_layer()
        for p in self.primitives:
            ctx.render(p)
        ctx.flatten()

        if filename is not None:
            ctx.dump(filename)
