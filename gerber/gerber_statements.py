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
from .utils import parse_gerber_value, write_gerber_value, decimal_string


__all__ = ['FSParamStmt', 'MOParamStmt', 'IPParamStmt', 'OFParamStmt',
           'LPParamStmt', 'ADParamStmt', 'AMParamStmt', 'INParamStmt',
           'LNParamStmt', 'CoordStmt', 'ApertureStmt', 'CommentStmt',
           'EofStmt', 'QuadrantModeStmt', 'RegionModeStmt', 'UnknownStmt',
           'ParamStmt']


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
    def __init__(self, stype):
        self.type = stype

    def __str__(self):
        s = "<{0} ".format(self.__class__.__name__)

        for key, value in self.__dict__.items():
            s += "{0}={1} ".format(key, value)

        s = s.rstrip() + ">"
        return s


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
    def from_dict(cls, stmt_dict):
        """
        """
        param = stmt_dict.get('param')
        zeros = 'leading' if stmt_dict.get('zero') == 'L' else 'trailing'
        notation = 'absolute' if stmt_dict.get('notation') == 'A' else 'incremental'
        x = map(int, stmt_dict.get('x'))
        fmt = (x[0], x[1])
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
            Zero-suppression mode. May be either 'leading' or 'trailing'

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

    def to_gerber(self):
        zero_suppression = 'L' if self.zero_suppression == 'leading' else 'T'
        notation = 'A' if self.notation == 'absolute' else 'I'
        fmt = ''.join(map(str, self.format))
        return '%FS{0}{1}X{2}Y{3}*%'.format(zero_suppression, notation,
                                            fmt, fmt)

    def __str__(self):
        return ('<Format Spec: %d:%d %s zero suppression %s notation>' %
                (self.format[0], self.format[1], self.zero_suppression,
                 self.notation))


class MOParamStmt(ParamStmt):
    """ MO - Gerber Mode (measurement units) Statement.
    """

    @classmethod
    def from_dict(cls, stmt_dict):
        param = stmt_dict.get('param')
        if stmt_dict.get('mo').lower() == 'in':
            mo = 'inch'
        elif stmt_dict.get('mo').lower() == 'mm':
            mo = 'metric'
        else:
            mo = None
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

    def to_gerber(self):
        mode = 'MM' if self.mode == 'metric' else 'IN'
        return '%MO{0}*%'.format(mode)

    def __str__(self):
        mode_str = 'millimeters' if self.mode == 'metric' else 'inches'
        return ('<Mode: %s>' % mode_str)


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

    def to_gerber(self):
        ip = 'POS' if self.ip == 'positive' else 'NEG'
        return '%IP{0}*%'.format(ip)

    def __str__(self):
        return ('<Image Polarity: %s>' % self.ip)


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

    def to_gerber(self):
        ret = '%OF'
        if self.a is not None:
            ret += 'A' + decimal_string(self.a, precision=5)
        if self.b is not None:
            ret += 'B' + decimal_string(self.b, precision=5)
        return ret + '*%'

    def __str__(self):
        offset_str = ''
        if self.a is not None:
            offset_str += ('X: %f' % self.a)
        if self.b is not None:
            offset_str += ('Y: %f' % self.b)
        return ('<Offset: %s>' % offset_str)


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

    def to_gerber(self):
        lp = 'C' if self.lp == 'clear' else 'D'
        return '%LP{0}*%'.format(lp)

    def __str__(self):
        return '<Level Polarity: %s>' % self.lp


class ADParamStmt(ParamStmt):
    """ AD - Gerber Aperture Definition Statement
    """

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
        ParamStmt : LPParamStmt
            Initialized LPParamStmt class.

        """
        ParamStmt.__init__(self, param)
        self.d = d
        self.shape = shape
        if modifiers is not None:
            self.modifiers = [[x for x in m.split("X")] for m in modifiers.split(",")]
        else:
            self.modifiers = []

    def to_gerber(self):
        return '%ADD{0}{1},{2}*%'.format(self.d, self.shape,
                                         ','.join(['X'.join(e) for e in self.modifiers]))

    def __str__(self):
        if self.shape == 'C':
            shape = 'circle'
        elif self.shape == 'R':
            shape = 'rectangle'
        elif self.shape == 'O':
            shape = 'oblong'
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

    def to_gerber(self):
        return '%AM{0}*{1}*%'.format(self.name, self.macro)

    def __str__(self):
        return '<Aperture Macro %s: %s>' % (self.name, self.macro)


class INParamStmt(ParamStmt):
    """ IN - Image Name Statement
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

    def to_gerber(self):
        return '%IN{0}*%'.format(self.name)

    def __str__(self):
        return '<Image Name: %s>' % self.name


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

    def to_gerber(self):
        return '%LN{0}*%'.format(self.name)

    def __str__(self):
        return '<Level Name: %s>' % self.name


class CoordStmt(Statement):
    """ Coordinate Data Block
    """

    @classmethod
    def from_dict(cls, stmt_dict, settings):
        zeros = settings.zero_suppression
        format = settings.format
        function = stmt_dict['function']
        x = stmt_dict.get('x')
        y = stmt_dict.get('y')
        i = stmt_dict.get('i')
        j = stmt_dict.get('j')
        op = stmt_dict.get('op')

        if x is not None:
            x = parse_gerber_value(stmt_dict.get('x'),
                                   format, zeros)
        if y is not None:
            y = parse_gerber_value(stmt_dict.get('y'),
                                   format, zeros)
        if i is not None:
            i = parse_gerber_value(stmt_dict.get('i'),
                                   format, zeros)
        if j is not None:
            j = parse_gerber_value(stmt_dict.get('j'),
                                   format, zeros)
        return cls(function, x, y, i, j, op, settings)

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
        self.zero_suppression = settings.zero_suppression
        self.format = settings.format
        self.function = function
        self.x = x
        self.y = y
        self.i = i
        self.j = j
        self.op = op

    def to_gerber(self):
        ret = ''
        if self.function:
            ret += self.function
        if self.x is not None:
            ret += 'X{0}'.format(write_gerber_value(self.x, self.format, self.zero_suppression))
        if self.y is not None:
            ret += 'Y{0}'.format(write_gerber_value(self.y, self.format, self.zero_suppression))
        if self.i is not None:
            ret += 'I{0}'.format(write_gerber_value(self.i, self.format, self.zero_suppression))
        if self.j is not None:
            ret += 'J{0}'.format(write_gerber_value(self.j, self.format, self.zero_suppression))
        if self.op:
            ret += self.op
        return ret + '*'

    def __str__(self):
        coord_str = ''
        if self.function:
            coord_str += 'Fn: %s ' % self.function
        if self.x is not None:
            coord_str += 'X: %f ' % self.x
        if self.y is not None:
            coord_str += 'Y: %f ' % self.y
        if self.i is not None:
            coord_str += 'I: %f ' % self.i
        if self.j is not None:
            coord_str += 'J: %f ' % self.j
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


class ApertureStmt(Statement):
    """ Aperture Statement
    """
    def __init__(self, d, deprecated=None):
        Statement.__init__(self, "APERTURE")
        self.d = int(d)
        self.deprecated = True if deprecated is not None else False

    def to_gerber(self):
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
        self.comment = comment

    def to_gerber(self):
        return 'G04{0}*'.format(self.comment)

    def __str__(self):
        return '<Comment: %s>' % self.comment


class EofStmt(Statement):
    """ EOF Statement
    """
    def __init__(self):
        Statement.__init__(self, "EOF")

    def to_gerber(self):
        return 'M02*'

    def __str__(self):
        return '<EOF Statement>'


class QuadrantModeStmt(Statement):

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

    def to_gerber(self):
        return 'G74*' if self.mode == 'single-quadrant' else 'G75*'


class RegionModeStmt(Statement):

    @classmethod
    def from_gerber(cls, line):
        if 'G36' not in line and 'G37' not in line:
            raise ValueError('%s is not a valid region mode statement' % line)
        return (cls('on') if line[:3] == 'G36' else cls('off'))

    def __init__(self, mode):
        super(RegionModeStmt, self).__init__('RegionMode')
        mode = mode.lower()
        if mode not in ['on', 'off']:
            raise ValueError('Valid modes are "on" or "off"')
        self.mode = mode

    def to_gerber(self):
        return 'G36*' if self.mode == 'on' else 'G37*'


class UnknownStmt(Statement):
    """ Unknown Statement
    """
    def __init__(self, line):
        Statement.__init__(self, "UNKNOWN")
        self.line = line

    def to_gerber(self):
        return self.line
