#!/usr/bin/env python
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
Gerber (RS-274X) Statements
===========================
**Gerber RS-274X file statement classes**

"""
from .utils import (parse_gerber_value, write_gerber_value, decimal_string,
                    inch, metric)

from .am_statements import *
from .am_read import read_macro
from .am_eval import eval_macro
from .primitives import AMGroup


class Statement(object):
    """ Gerber statement Base class

    The statement class provides a type attribute.

    Parameters
    ----------
    type : string
        String identifying the statement type.

    Attributes
    ----------
    type : string
        String identifying the statement type.
    """

    def __init__(self, stype, units='inch'):
        self.type = stype
        self.units = units

    def __str__(self):
        s = "<{0} ".format(self.__class__.__name__)

        for key, value in self.__dict__.items():
            s += "{0}={1} ".format(key, value)

        s = s.rstrip() + ">"
        return s

    def to_inch(self):
        self.units = 'inch'

    def to_metric(self):
        self.units = 'metric'

    def offset(self, x_offset=0, y_offset=0):
        pass

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class ParamStmt(Statement):
    """ Gerber parameter statement Base class

    The parameter statement class provides a parameter type attribute.

    Parameters
    ----------
    param : string
        two-character code identifying the parameter statement type.

    Attributes
    ----------
    param : string
        Parameter type code
    """

    def __init__(self, param):
        Statement.__init__(self, "PARAM")
        self.param = param


class FSParamStmt(ParamStmt):
    """ FS - Gerber Format Specification Statement
    """

    @classmethod
    def from_settings(cls, settings):

        return cls('FS', settings.zero_suppression, settings.notation, settings.format)

    @classmethod
    def from_dict(cls, stmt_dict):
        """
        """
        param = stmt_dict.get('param')

        if stmt_dict.get('zero') == 'L':
            zeros = 'leading'
        elif stmt_dict.get('zero') == 'T':
            zeros = 'trailing'
        else:
            zeros = 'none'

        notation = 'absolute' if stmt_dict.get('notation') == 'A' else 'incremental'
        fmt = tuple(map(int, stmt_dict.get('x')))
        return cls(param, zeros, notation, fmt)

    def __init__(self, param, zero_suppression='leading',
                 notation='absolute', format=(2, 4)):
        """ Initialize FSParamStmt class

        .. note::
            The FS command specifies the format of the coordinate data. It
            must only be used once at the beginning of a file. It must be
            specified before the first use of coordinate data.

        Parameters
        ----------
        param : string
            Parameter.

        zero_suppression : string
            Zero-suppression mode. May be either 'leading', 'trailing' or 'none' (all zeros are present)

        notation : string
            Notation mode. May be either 'absolute' or 'incremental'

        format : tuple (int, int)
            Gerber precision format expressed as a tuple containing:
            (number of integer-part digits, number of decimal-part digits)

        Returns
        -------
        ParamStmt : FSParamStmt
            Initialized FSParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.zero_suppression = zero_suppression
        self.notation = notation
        self.format = format

    def to_gerber(self, settings=None):
        if settings:
            zero_suppression = 'L' if settings.zero_suppression == 'leading' else 'T'
            notation = 'A' if settings.notation == 'absolute' else 'I'
            fmt = ''.join(map(str, settings.format))
        else:
            zero_suppression = 'L' if self.zero_suppression == 'leading' else 'T'
            notation = 'A' if self.notation == 'absolute' else 'I'
            fmt = ''.join(map(str, self.format))

        return '%FS{0}{1}X{2}Y{3}*%'.format(zero_suppression, notation, fmt, fmt)

    def __str__(self):
        return ('<Format Spec: %d:%d %s zero suppression %s notation>' %
                (self.format[0], self.format[1], self.zero_suppression, self.notation))


class MOParamStmt(ParamStmt):
    """ MO - Gerber Mode (measurement units) Statement.
    """

    @classmethod
    def from_units(cls, units):
        return cls(None, units)

    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        if stmt_dict.get('mo') is None:
            mo = None
        elif stmt_dict.get('mo').lower() not in ('in', 'mm'):
            raise ValueError('Mode may be mm or in')
        elif stmt_dict.get('mo').lower() == 'in':
            mo = 'inch'
        else:
            mo = 'metric'
        return cls(param, mo)

    def __init__(self, param, mo):
        """ Initialize MOParamStmt class

        Parameters
        ----------
        param : string
            Parameter.

        mo : string
            Measurement units. May be either 'inch' or 'metric'

        Returns
        -------
        ParamStmt : MOParamStmt
            Initialized MOParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.mode = mo

    def to_gerber(self, settings=None):
        mode = 'MM' if self.mode == 'metric' else 'IN'
        return '%MO{0}*%'.format(mode)

    def to_inch(self):
        self.mode = 'inch'

    def to_metric(self):
        self.mode = 'metric'

    def __str__(self):
        mode_str = 'millimeters' if self.mode == 'metric' else 'inches'
        return ('<Mode: %s>' % mode_str)


class LPParamStmt(ParamStmt):
    """ LP - Gerber Level Polarity statement
    """

    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict['param']
        lp = 'clear' if stmt_dict.get('lp') == 'C' else 'dark'
        return cls(param, lp)

    def __init__(self, param, lp):
        """ Initialize LPParamStmt class

        Parameters
        ----------
        param : string
            Parameter

        lp : string
            Level polarity. May be either 'clear' or 'dark'

        Returns
        -------
        ParamStmt : LPParamStmt
            Initialized LPParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.lp = lp

    def to_gerber(self, settings=None):
        lp = 'C' if self.lp == 'clear' else 'D'
        return '%LP{0}*%'.format(lp)

    def __str__(self):
        return '<Level Polarity: %s>' % self.lp


class ADParamStmt(ParamStmt):
    """ AD - Gerber Aperture Definition Statement
    """

    @classmethod
    def rect(cls, dcode, width, height, hole_diameter=None, hole_width=None, hole_height=None):
        '''Create a rectangular aperture definition statement'''
        if hole_diameter is not None and hole_diameter > 0:
            return cls('AD', dcode, 'R', ([width, height, hole_diameter],))
        elif (hole_width is not None and hole_width > 0
              and hole_height is not None and hole_height > 0):
            return cls('AD', dcode, 'R', ([width, height, hole_width, hole_height],))
        return cls('AD', dcode, 'R', ([width, height],))

    @classmethod
    def circle(cls, dcode, diameter, hole_diameter=None, hole_width=None, hole_height=None):
        '''Create a circular aperture definition statement'''
        if hole_diameter is not None and hole_diameter > 0:
            return cls('AD', dcode, 'C', ([diameter, hole_diameter],))
        elif (hole_width is not None and hole_width > 0
              and hole_height is not None and hole_height > 0):
            return cls('AD', dcode, 'C', ([diameter, hole_width, hole_height],))
        return cls('AD', dcode, 'C', ([diameter],))

    @classmethod
    def obround(cls, dcode, width, height, hole_diameter=None, hole_width=None, hole_height=None):
        '''Create an obround aperture definition statement'''
        if hole_diameter is not None and hole_diameter > 0:
            return cls('AD', dcode, 'O', ([width, height, hole_diameter],))
        elif (hole_width is not None and hole_width > 0
              and hole_height is not None and hole_height > 0):
            return cls('AD', dcode, 'O', ([width, height, hole_width, hole_height],))
        return cls('AD', dcode, 'O', ([width, height],))

    @classmethod
    def polygon(cls, dcode, diameter, num_vertices, rotation, hole_diameter=None, hole_width=None, hole_height=None):
        '''Create a polygon aperture definition statement'''
        if hole_diameter is not None and hole_diameter > 0:
            return cls('AD', dcode, 'P', ([diameter, num_vertices, rotation, hole_diameter],))
        elif (hole_width is not None and hole_width > 0
              and hole_height is not None and hole_height > 0):
            return cls('AD', dcode, 'P', ([diameter, num_vertices, rotation, hole_width, hole_height],))
        return cls('AD', dcode, 'P', ([diameter, num_vertices, rotation],))


    @classmethod
    def macro(cls, dcode, name):
        return cls('AD', dcode, name, '')

    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        d = int(stmt_dict.get('d'))
        shape = stmt_dict.get('shape')
        modifiers = stmt_dict.get('modifiers')
        return cls(param, d, shape, modifiers)

    def __init__(self, param, d, shape, modifiers):
        """ Initialize ADParamStmt class

        Parameters
        ----------
        param : string
            Parameter code

        d : int
            Aperture D-code

        shape : string
            aperture name

        modifiers : list of lists of floats
            Shape modifiers

        Returns
        -------
        ParamStmt : ADParamStmt
            Initialized ADParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.d = d
        self.shape = shape
        if isinstance(modifiers, tuple):
            self.modifiers = modifiers
        elif modifiers:
            self.modifiers = [tuple([float(x) for x in m.split("X") if len(x)])
                              for m in modifiers.split(",") if len(m)]
        else:
            self.modifiers = [tuple()]

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            self.modifiers = [tuple([inch(x) for x in modifier])
                              for modifier in self.modifiers]

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            self.modifiers = [tuple([metric(x) for x in modifier])
                              for modifier in self.modifiers]

    def to_gerber(self, settings=None):
        if any(self.modifiers):
            return '%ADD{0}{1},{2}*%'.format(self.d, self.shape, ','.join(['X'.join(["%.4g" % x for x in modifier]) for modifier in self.modifiers]))
        else:
            return '%ADD{0}{1}*%'.format(self.d, self.shape)

    def __str__(self):
        if self.shape == 'C':
            shape = 'circle'
        elif self.shape == 'R':
            shape = 'rectangle'
        elif self.shape == 'O':
            shape = 'obround'
        else:
            shape = self.shape

        return '<Aperture Definition: %d: %s>' % (self.d, shape)


class AMParamStmt(ParamStmt):
    """ AM - Aperture Macro Statement
    """

    @classmethod
    def from_dict(cls, stmt_dict):
        return cls(**stmt_dict)

    def __init__(self, param, name, macro):
        """ Initialize AMParamStmt class

        Parameters
        ----------
        param : string
            Parameter code

        name : string
            Aperture macro name

        macro : string
            Aperture macro string

        Returns
        -------
        ParamStmt : AMParamStmt
            Initialized AMParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.name = name
        self.macro = macro

        self.instructions = self.read(macro)
        self.primitives = []

    def read(self, macro):
        return read_macro(macro)

    def build(self, modifiers=[[]]):
        self.primitives = []

        for primitive in eval_macro(self.instructions, modifiers[0]):
            if primitive[0] == '0':
                self.primitives.append(AMCommentPrimitive.from_gerber(primitive))
            elif primitive[0] == '1':
                self.primitives.append(AMCirclePrimitive.from_gerber(primitive))
            elif primitive[0:2] in ('2,', '20'):
                self.primitives.append(AMVectorLinePrimitive.from_gerber(primitive))
            elif primitive[0:2] == '21':
                self.primitives.append(AMCenterLinePrimitive.from_gerber(primitive))
            elif primitive[0:2] == '22':
                self.primitives.append(AMLowerLeftLinePrimitive.from_gerber(primitive))
            elif primitive[0] == '4':
                self.primitives.append(AMOutlinePrimitive.from_gerber(primitive))
            elif primitive[0] == '5':
                self.primitives.append(AMPolygonPrimitive.from_gerber(primitive))
            elif primitive[0] == '6':
                self.primitives.append(AMMoirePrimitive.from_gerber(primitive))
            elif primitive[0] == '7':
                self.primitives.append(
                    AMThermalPrimitive.from_gerber(primitive))
            else:
                self.primitives.append(
                    AMUnsupportPrimitive.from_gerber(primitive))

        return AMGroup(self.primitives, stmt=self, units=self.units)

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            for primitive in self.primitives:
                primitive.to_inch()

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            for primitive in self.primitives:
                primitive.to_metric()

    def to_gerber(self, settings=None):
        return '%AM{0}*{1}%'.format(self.name, "".join([primitive.to_gerber() for primitive in self.primitives]))

    def __str__(self):
        return '<Aperture Macro %s: %s>' % (self.name, self.macro)


class ASParamStmt(ParamStmt):
    """ AS - Axis Select. (Deprecated)
    """
    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        mode = stmt_dict.get('mode')
        return cls(param, mode)

    def __init__(self, param, mode):
        """ Initialize ASParamStmt class

        Parameters
        ----------
        param : string
            Parameter string.

        mode : string
            Axis select. May be either 'AXBY' or 'AYBX'

        Returns
        -------
        ParamStmt : ASParamStmt
            Initialized ASParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.mode = mode

    def to_gerber(self, settings=None):
        return '%AS{0}*%'.format(self.mode)

    def __str__(self):
        return ('<Axis Select: %s>' % self.mode)


class INParamStmt(ParamStmt):
    """ IN - Image Name Statement (Deprecated)
    """
    @classmethod
    def from_dict(cls, stmt_dict):
        return cls(**stmt_dict)

    def __init__(self, param, name):
        """ Initialize INParamStmt class

        Parameters
        ----------
        param : string
            Parameter code

        name : string
            Image name

        Returns
        -------
        ParamStmt : INParamStmt
            Initialized INParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.name = name

    def to_gerber(self, settings=None):
        return '%IN{0}*%'.format(self.name)

    def __str__(self):
        return '<Image Name: %s>' % self.name


class IPParamStmt(ParamStmt):
    """ IP - Gerber Image Polarity Statement. (Deprecated)
    """
    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        ip = 'positive' if stmt_dict.get('ip') == 'POS' else 'negative'
        return cls(param, ip)

    def __init__(self, param, ip):
        """ Initialize IPParamStmt class

        Parameters
        ----------
        param : string
            Parameter string.

        ip : string
            Image polarity. May be either'positive' or 'negative'

        Returns
        -------
        ParamStmt : IPParamStmt
            Initialized IPParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.ip = ip

    def to_gerber(self, settings=None):
        ip = 'POS' if self.ip == 'positive' else 'NEG'
        return '%IP{0}*%'.format(ip)

    def __str__(self):
        return ('<Image Polarity: %s>' % self.ip)


class IRParamStmt(ParamStmt):
    """ IR - Image Rotation Param (Deprecated)
    """
    @classmethod
    def from_dict(cls, stmt_dict):
        angle = int(stmt_dict['angle'])
        return cls(stmt_dict['param'], angle)

    def __init__(self, param, angle):
        """ Initialize IRParamStmt class

        Parameters
        ----------
        param : string
            Parameter code

        angle : int
            Image angle

        Returns
        -------
        ParamStmt : IRParamStmt
            Initialized IRParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.angle = angle

    def to_gerber(self, settings=None):
        return '%IR{0}*%'.format(self.angle)

    def __str__(self):
        return '<Image Angle: %s>' % self.angle


class MIParamStmt(ParamStmt):
    """ MI - Image Mirror Param (Deprecated)
    """
    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        a = int(stmt_dict.get('a', 0))
        b = int(stmt_dict.get('b', 0))
        return cls(param, a, b)

    def __init__(self, param, a, b):
        """ Initialize MIParamStmt class

        Parameters
        ----------
        param : string
            Parameter code

        a : int
            Mirror for A output devices axis (0=disabled, 1=mirrored)

        b : int
            Mirror for B output devices axis (0=disabled, 1=mirrored)

        Returns
        -------
        ParamStmt : MIParamStmt
            Initialized MIParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.a = a
        self.b = b

    def to_gerber(self, settings=None):
        ret = "%MI"
        if self.a is not None:
            ret += "A{0}".format(self.a)
        if self.b is not None:
            ret += "B{0}".format(self.b)
        ret += "*%"
        return ret

    def __str__(self):
        return '<Image Mirror: A=%d B=%d>' % (self.a, self.b)


class OFParamStmt(ParamStmt):
    """ OF - Gerber Offset statement (Deprecated)
    """

    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        a = float(stmt_dict.get('a', 0))
        b = float(stmt_dict.get('b', 0))
        return cls(param, a, b)

    def __init__(self, param, a, b):
        """ Initialize OFParamStmt class

        Parameters
        ----------
        param : string
            Parameter

        a : float
            Offset along the output device A axis

        b : float
            Offset along the output device B axis

        Returns
        -------
        ParamStmt : OFParamStmt
            Initialized OFParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.a = a
        self.b = b

    def to_gerber(self, settings=None):
        ret = '%OF'
        if self.a is not None:
            ret += 'A' + decimal_string(self.a, precision=5)
        if self.b is not None:
            ret += 'B' + decimal_string(self.b, precision=5)
        return ret + '*%'

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.a is not None:
                self.a = inch(self.a)
            if self.b is not None:
                self.b = inch(self.b)

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.a is not None:
                self.a = metric(self.a)
            if self.b is not None:
                self.b = metric(self.b)

    def offset(self, x_offset=0, y_offset=0):
        if self.a is not None:
            self.a += x_offset
        if self.b is not None:
            self.b += y_offset

    def __str__(self):
        offset_str = ''
        if self.a is not None:
            offset_str += ('X: %f ' % self.a)
        if self.b is not None:
            offset_str += ('Y: %f ' % self.b)
        return ('<Offset: %s>' % offset_str)


class SFParamStmt(ParamStmt):
    """ SF - Scale Factor Param (Deprecated)
    """

    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        a = float(stmt_dict.get('a', 1))
        b = float(stmt_dict.get('b', 1))
        return cls(param, a, b)

    def __init__(self, param, a, b):
        """ Initialize OFParamStmt class

        Parameters
        ----------
        param : string
            Parameter

        a : float
            Scale factor for the output device A axis

        b : float
            Scale factor for the output device B axis

        Returns
        -------
        ParamStmt : SFParamStmt
            Initialized SFParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.a = a
        self.b = b

    def to_gerber(self, settings=None):
        ret = '%SF'
        if self.a is not None:
            ret += 'A' + decimal_string(self.a, precision=5)
        if self.b is not None:
            ret += 'B' + decimal_string(self.b, precision=5)
        return ret + '*%'

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.a is not None:
                self.a = inch(self.a)
            if self.b is not None:
                self.b = inch(self.b)

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.a is not None:
                self.a = metric(self.a)
            if self.b is not None:
                self.b = metric(self.b)

    def offset(self, x_offset=0, y_offset=0):
        if self.a is not None:
            self.a += x_offset
        if self.b is not None:
            self.b += y_offset

    def __str__(self):
        scale_factor = ''
        if self.a is not None:
            scale_factor += ('X: %g ' % self.a)
        if self.b is not None:
            scale_factor += ('Y: %g' % self.b)
        return ('<Scale Factor: %s>' % scale_factor)


class LNParamStmt(ParamStmt):
    """ LN - Level Name Statement (Deprecated)
    """
    @classmethod
    def from_dict(cls, stmt_dict):
        return cls(**stmt_dict)

    def __init__(self, param, name):
        """ Initialize LNParamStmt class

        Parameters
        ----------
        param : string
            Parameter code

        name : string
            Level name

        Returns
        -------
        ParamStmt : LNParamStmt
            Initialized LNParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.name = name

    def to_gerber(self, settings=None):
        return '%LN{0}*%'.format(self.name)

    def __str__(self):
        return '<Level Name: %s>' % self.name


class DeprecatedStmt(Statement):
    """ Unimportant deprecated statement, will be parsed but not emitted.
    """
    @classmethod
    def from_gerber(cls, line):
        return cls(line)

    def __init__(self, line):
        """ Initialize DeprecatedStmt class

        Parameters
        ----------
        line : string
            Deprecated statement text

        Returns
        -------
        DeprecatedStmt
            Initialized DeprecatedStmt class.

        """
        Statement.__init__(self, "DEPRECATED")
        self.line = line

    def to_gerber(self, settings=None):
        return self.line

    def __str__(self):
        return '<Deprecated Statement: \'%s\'>' % self.line


class CoordStmt(Statement):
    """ Coordinate Data Block
    """

    OP_DRAW = 'D01'
    OP_MOVE = 'D02'
    OP_FLASH = 'D03'

    FUNC_LINEAR = 'G01'
    FUNC_ARC_CW = 'G02'
    FUNC_ARC_CCW = 'G03'

    @classmethod
    def from_dict(cls, stmt_dict, settings):
        function = stmt_dict['function']
        x = stmt_dict.get('x')
        y = stmt_dict.get('y')
        i = stmt_dict.get('i')
        j = stmt_dict.get('j')
        op = stmt_dict.get('op')

        if x is not None:
            x = parse_gerber_value(stmt_dict.get('x'), settings.format,
                                   settings.zero_suppression)
        if y is not None:
            y = parse_gerber_value(stmt_dict.get('y'), settings.format,
                                   settings.zero_suppression)
        if i is not None:
            i = parse_gerber_value(stmt_dict.get('i'), settings.format,
                                   settings.zero_suppression)
        if j is not None:
            j = parse_gerber_value(stmt_dict.get('j'), settings.format,
                                   settings.zero_suppression)
        return cls(function, x, y, i, j, op, settings)

    @classmethod
    def move(cls, func, point):
        if point:
            return cls(func, point[0], point[1], None, None, CoordStmt.OP_MOVE, None)
        # No point specified, so just write the function. This is normally for ending a region (D02*)
        return cls(func, None, None, None, None, CoordStmt.OP_MOVE, None)

    @classmethod
    def line(cls, func, point):
        return cls(func, point[0], point[1], None, None, CoordStmt.OP_DRAW, None)

    @classmethod
    def mode(cls, func):
        return cls(func, None, None, None, None, None, None)

    @classmethod
    def arc(cls, func, point, center):
        return cls(func, point[0], point[1], center[0], center[1], CoordStmt.OP_DRAW, None)

    @classmethod
    def flash(cls, point):
        if point:
            return cls(None, point[0], point[1], None, None, CoordStmt.OP_FLASH, None)
        else:
            return cls(None, None, None, None, None, CoordStmt.OP_FLASH, None)

    def __init__(self, function, x, y, i, j, op, settings):
        """ Initialize CoordStmt class

        Parameters
        ----------
        function : string
            function

        x : float
            X coordinate

        y : float
            Y coordinate

        i : float
            Coordinate offset in the X direction

        j : float
            Coordinate offset in the Y direction

        op : string
            Operation code

        settings : dict {'zero_suppression', 'format'}
            Gerber file coordinate format

        Returns
        -------
        Statement : CoordStmt
            Initialized CoordStmt class.

        """
        Statement.__init__(self, "COORD")
        self.function = function
        self.x = x
        self.y = y
        self.i = i
        self.j = j
        self.op = op

    def to_gerber(self, settings=None):
        ret = ''
        if self.function:
            ret += self.function
        if self.x is not None:
            ret += 'X{0}'.format(write_gerber_value(self.x, settings.format,
                                                    settings.zero_suppression))
        if self.y is not None:
            ret += 'Y{0}'.format(write_gerber_value(self.y, settings.format,
                                                    settings.zero_suppression))
        if self.i is not None:
            ret += 'I{0}'.format(write_gerber_value(self.i, settings.format,
                                                    settings.zero_suppression))
        if self.j is not None:
            ret += 'J{0}'.format(write_gerber_value(self.j, settings.format,
                                                    settings.zero_suppression))
        if self.op:
            ret += self.op
        return ret + '*'

    def to_inch(self):
        if self.units == 'metric':
            self.units = 'inch'
            if self.x is not None:
                self.x = inch(self.x)
            if self.y is not None:
                self.y = inch(self.y)
            if self.i is not None:
                self.i = inch(self.i)
            if self.j is not None:
                self.j = inch(self.j)
            if self.function == "G71":
                self.function = "G70"

    def to_metric(self):
        if self.units == 'inch':
            self.units = 'metric'
            if self.x is not None:
                self.x = metric(self.x)
            if self.y is not None:
                self.y = metric(self.y)
            if self.i is not None:
                self.i = metric(self.i)
            if self.j is not None:
                self.j = metric(self.j)
            if self.function == "G70":
                self.function = "G71"

    def offset(self, x_offset=0, y_offset=0):
        if self.x is not None:
            self.x += x_offset
        if self.y is not None:
            self.y += y_offset
        if self.i is not None:
            self.i += x_offset
        if self.j is not None:
            self.j += y_offset

    def __str__(self):
        coord_str = ''
        if self.function:
            coord_str += 'Fn: %s ' % self.function
        if self.x is not None:
            coord_str += 'X: %g ' % self.x
        if self.y is not None:
            coord_str += 'Y: %g ' % self.y
        if self.i is not None:
            coord_str += 'I: %g ' % self.i
        if self.j is not None:
            coord_str += 'J: %g ' % self.j
        if self.op:
            if self.op == 'D01':
                op = 'Lights On'
            elif self.op == 'D02':
                op = 'Lights Off'
            elif self.op == 'D03':
                op = 'Flash'
            else:
                op = self.op
            coord_str += 'Op: %s' % op

        return '<Coordinate Statement: %s>' % coord_str

    @property
    def only_function(self):
        """
        Returns if the statement only set the function.
        """

        # TODO I would like to refactor this so that the function is handled separately and then
        # TODO this isn't required
        return self.function != None and self.op == None and self.x == None and self.y == None and self.i == None and self.j == None


class ApertureStmt(Statement):
    """ Aperture Statement
    """

    def __init__(self, d, deprecated=None):
        Statement.__init__(self, "APERTURE")
        self.d = int(d)
        self.deprecated = True if deprecated is not None and deprecated is not False else False

    def to_gerber(self, settings=None):
        if self.deprecated:
            return 'G54D{0}*'.format(self.d)
        else:
            return 'D{0}*'.format(self.d)

    def __str__(self):
        return '<Aperture: %d>' % self.d


class CommentStmt(Statement):
    """ Comment Statment
    """

    def __init__(self, comment):
        Statement.__init__(self, "COMMENT")
        self.comment = comment if comment is not None else ""

    def to_gerber(self, settings=None):
        return 'G04{0}*'.format(self.comment)

    def __str__(self):
        return '<Comment: %s>' % self.comment


class EofStmt(Statement):
    """ EOF Statement
    """

    def __init__(self):
        Statement.__init__(self, "EOF")

    def to_gerber(self, settings=None):
        return 'M02*'

    def __str__(self):
        return '<EOF Statement>'


class QuadrantModeStmt(Statement):

    @classmethod
    def single(cls):
        return cls('single-quadrant')

    @classmethod
    def multi(cls):
        return cls('multi-quadrant')

    @classmethod
    def from_gerber(cls, line):
        if 'G74' not in line and 'G75' not in line:
            raise ValueError('%s is not a valid quadrant mode statement'
                             % line)
        return (cls('single-quadrant') if line[:3] == 'G74'
                else cls('multi-quadrant'))

    def __init__(self, mode):
        super(QuadrantModeStmt, self).__init__('QuadrantMode')
        mode = mode.lower()
        if mode not in ['single-quadrant', 'multi-quadrant']:
            raise ValueError('Quadrant mode must be "single-quadrant" \
                             or "multi-quadrant"')
        self.mode = mode

    def to_gerber(self, settings=None):
        return 'G74*' if self.mode == 'single-quadrant' else 'G75*'


class RegionModeStmt(Statement):

    @classmethod
    def from_gerber(cls, line):
        if 'G36' not in line and 'G37' not in line:
            raise ValueError('%s is not a valid region mode statement' % line)
        return (cls('on') if line[:3] == 'G36' else cls('off'))

    @classmethod
    def on(cls):
        return cls('on')

    @classmethod
    def off(cls):
        return cls('off')

    def __init__(self, mode):
        super(RegionModeStmt, self).__init__('RegionMode')
        mode = mode.lower()
        if mode not in ['on', 'off']:
            raise ValueError('Valid modes are "on" or "off"')
        self.mode = mode

    def to_gerber(self, settings=None):
        return 'G36*' if self.mode == 'on' else 'G37*'


class UnknownStmt(Statement):
    """ Unknown Statement
    """

    def __init__(self, line):
        Statement.__init__(self, "UNKNOWN")
        self.line = line

    def to_gerber(self, settings=None):
        return self.line

    def __str__(self):
        return '<Unknown Statement: \'%s\'>' % self.line
