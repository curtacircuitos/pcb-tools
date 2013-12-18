#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


def red(s):
    return '\033[1;31m{0}\033[0;m'.format(s)


class Statement:
    def __init__(self):
        pass


class ParamStmt(Statement):
    def __init__(self, type):
        self.type = type


class FSParamStmt(ParamStmt):
    def __init__(self, type, zero, notation, x, y):
        ParamStmt.__init__(self, type)
        self.zero = zero
        self.notation = notation
        self.x = x
        self.y = y


class MOParamStmt(ParamStmt):
    def __init__(self, type, mo):
        ParamStmt.__init__(self, type)
        self.mo = mo


class IPParamStmt(ParamStmt):
    def __init__(self, type, ip):
        ParamStmt.__init__(self, type)
        self.ip = ip


class OFParamStmt(ParamStmt):
    def __init__(self, type, a, b):
        ParamStmt.__init__(self, type)
        self.a = a
        self.b = b


class LPParamStmt(ParamStmt):
    def __init__(self, type, lp):
        ParamStmt.__init__(self, type)
        self.lp = lp


class ADParamStmt(ParamStmt):
    def __init__(self, type, d, shape):
        ParamStmt.__init__(self, type)
        self.d = d
        self.shape = shape


class ADCircleParamStmt(ADParamStmt):
    def __init__(self, type, d, shape, definition):
        ADParamStmt.__init__(self, type, d, shape)
        self.definition = definition


class ADRectParamStmt(ADParamStmt):
    def __init__(self, type, d, shape, definition):
        ADParamStmt.__init__(self, type, d, shape)
        self.definition = definition


class ADObroundParamStmt(ADParamStmt):
    def __init__(self, type, d, shape, definition):
        ADParamStmt.__init__(self, type, d, shape)
        self.definition = definition


class ADPolyParamStmt(ADParamStmt):
    def __init__(self, type, d, shape, definition):
        ADParamStmt.__init__(self, type, d, shape)
        self.definition = definition


class ADMacroParamStmt(ADParamStmt):
    def __init__(self, type, d, name, definition):
        ADParamStmt.__init__(self, type, d, "M")
        self.name = name
        self.definition = definition


class AMParamStmt(ParamStmt):
    def __init__(self, type, name, macro):
        ParamStmt.__init__(self, type)
        self.name = name
        self.macro = macro


class INParamStmt(ParamStmt):
    def __init__(self, type, name):
        ParamStmt.__init__(self, type)
        self.name = name


class LNParamStmt(ParamStmt):
    def __init__(self, type, name):
        ParamStmt.__init__(self, type)
        self.name = name


class CoordStmt(Statement):
    def __init__(self, function, x, y, i, j, op):
        self.function = function
        self.x = x
        self.y = y
        self.i = i
        self.j = j
        self.op = op


class ApertureStmt(Statement):
    def __init__(self, d):
        self.d = int(d)


class CommentStmt(Statement):
    def __init__(self, comment):
        self.comment = comment


class EofStmt(Statement):
    pass


class UnknownStmt(Statement):
    def __init__(self, line):
        self.line = line


IMAGE_POLARITY_POSITIVE = 1
IMAGE_POLARITY_NEGATIVE = 2

LEVEL_POLARITY_DARK = 1
LEVEL_POLARITY_CLEAR = 2

NOTATION_ABSOLUTE = 1
NOTATION_INCREMENTAL = 2


class GerberCoordFormat:

    def __init__(self, zeroes, x, y):
        self.omit_leading_zeroes = True if zeroes == "L" else False
        self.omit_trailing_zeroes = True if zeroes == "T" else False
        self.x_int_digits, self.x_dec_digits = [int(d) for d in x]
        self.y_int_digits, self.y_dec_digits = [int(d) for d in y]

    def resolve(self, x, y):
        return x, y


class GerberContext:
    coord_format = None
    coord_notation = NOTATION_ABSOLUTE

    unit = None

    x = 0
    y = 0

    current_aperture = 0
    interpolation = None

    region_mode = False
    quadrant_mode = False

    image_polarity = IMAGE_POLARITY_POSITIVE
    level_polarity = LEVEL_POLARITY_DARK

    steps = (1, 1)
    repeat = (None, None)

    def __init__(self):
        pass

    def set_coord_format(self, zeroes, x, y):
        self.coord_format = GerberCoordFormat(zeroes, x, y)

    def set_coord_notation(self, notation):
        self.coord_notation = NOTATION_ABSOLUTE if notation == "A" else NOTATION_INCREMENTAL

    def set_image_polarity(self, polarity):
        self.image_polarity = IMAGE_POLARITY_POSITIVE if polarity == "POS" else IMAGE_POLARITY_NEGATIVE

    def set_level_polarity(self, polarity):
        self.level_polarity = LEVEL_POLARITY_DARK if polarity == "D" else LEVEL_POLARITY_CLEAR

    def move(self, x, y):
        self.x = x
        self.y = y

    def aperture(self, d):
        self.current_aperture = d


class Gerber:
    NUMBER = r"[\+-]?\d+"
    FUNCTION = r"G\d{2}"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"
    NAME = "[a-zA-Z_$][a-zA-Z_$0-9]+"

    COORD_OP = r"D[0]?[123]"

    FS = r"(?P<type>FS)(?P<zero>(L|T))(?P<notation>(A|I))X(?P<x>[0-7][0-7])Y(?P<y>[0-7][0-7])"
    MO = r"(?P<type>MO)(?P<mo>(MM|IN))"
    IP = r"(?P<type>IP)(?P<ip>(POS|NEG))"
    LP = r"(?P<type>LP)(?P<lp>(D|C))"
    AD_CIRCLE = r"(?P<type>ADD)(?P<d>\d+)(?P<shape>C)(?P<definition>.*)"
    AD_RECT = r"(?P<type>ADD)(?P<d>\d+)(?P<shape>R)(?P<definition>.*)"
    AD_OBROUND = r"(?P<type>ADD)(?P<d>\d+)(?P<shape>O)(?P<definition>.*)"
    AD_POLY = r"(?P<type>ADD)(?P<d>\d+)(?P<shape>P)(?P<definition>.*)"
    AD_MACRO = r"(?P<type>ADD)(?P<d>\d+)(?P<name>[^CROP,].*)(?P<definition>.*)".format(name=NAME)
    AM = r"(?P<type>AM)(?P<name>{name})\*(?P<macro>.*)".format(name=NAME)

    # begin deprecated
    OF = r"(?P<type>OF)(A(?P<a>[+-]?\d+(.?\d*)))?(B(?P<b>[+-]?\d+(.?\d*)))?"
    IN = r"(?P<type>IN)(?P<name>.*)"
    LN = r"(?P<type>LN)(?P<name>.*)"
    # end deprecated

    PARAMS = (FS, MO, IP, LP, AD_CIRCLE, AD_RECT, AD_OBROUND, AD_MACRO, AD_POLY, AM, OF, IN, LN)
    PARAM_STMT = [re.compile(r"%{0}\*%".format(p)) for p in PARAMS]

    COORD_STMT = re.compile((
        r"(?P<function>{function})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, function=FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(G54)?D(?P<d>\d+)\*")

    COMMENT_STMT = re.compile(r"G04(?P<comment>{string})(\*)?".format(string=STRING))

    EOF_STMT = re.compile(r"(?P<eof>M02)\*")

    def __init__(self):
        self.tokens = []
        self.ctx = GerberContext()

    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        for token in self._tokenize(data):
            self._evaluate(token)

    def _tokenize(self, data):
        multiline = None

        for i, line in enumerate(data):
            # remove EOL
            if multiline:
                line = multiline + line.strip()
            else:
                line = line.strip()

            # skip empty lines
            if not len(line):
                continue

            # deal with multi-line parameters
            if line.startswith("%") and not line.endswith("%"):
                multiline = line
                continue
            else:
                multiline = None

            # coord
            coords = self._match_many(self.COORD_STMT, line)
            if coords:
                for coord in coords:
                    yield CoordStmt(**coord)
                continue

            # aperture selection
            aperture = self._match_one(self.APERTURE_STMT, line)
            if aperture:
                yield ApertureStmt(**aperture)
                continue

            # comment
            comment = self._match_one(self.COMMENT_STMT, line)
            if comment:
                yield CommentStmt(comment["comment"])
                continue

            # parameter
            param = self._match_one_from_many(self.PARAM_STMT, line)
            if param:
                if param["type"] == "FS":
                    yield FSParamStmt(**param)
                elif param["type"] == "MO":
                    yield MOParamStmt(**param)
                elif param["type"] == "IP":
                    yield IPParamStmt(**param)
                elif param["type"] == "LP":
                    yield LPParamStmt(**param)
                elif param["type"] == "AD":
                    if param["shape"] == "C":
                        yield ADCircleParamStmt(**param)
                    elif param["shape"] == "R":
                        yield ADRectParamStmt(**param)
                    elif param["shape"] == "O":
                        yield ADObroundParamStmt(**param)
                    elif param["shape"] == "P":
                        yield ADPolyParamStmt(**param)
                    else:
                        yield ADMacroParamStmt(**param)
                elif param["type"] == "AM":
                    yield AMParamStmt(**param)
                elif param["type"] == "OF":
                    yield OFParamStmt(**param)
                elif param["type"] == "IN":
                    yield INParamStmt(**param)
                elif param["type"] == "LN":
                    yield LNParamStmt(**param)
                else:
                    yield UnknownStmt(line)

                continue

            # eof
            eof = self._match_one(self.EOF_STMT, line)
            if eof:
                yield EofStmt()
                continue

            print red("UNKNOWN TOKEN")
            print "{0}:'{1}'".format(red(str(i+1)), line)

            if False:
                print self.COORD_STMT.pattern
                print self.APERTURE_STMT.pattern
                print self.COMMENT_STMT.pattern
                print self.EOF_STMT.pattern
                for i in self.PARAM_STMT:
                    print i.pattern

            yield UnknownStmt(line)

    def _match_one(self, expr, data):
        match = expr.match(data)
        if match is None:
            return {}
        else:
            return match.groupdict()

    def _match_one_from_many(self, exprs, data):
        for expr in exprs:
            match = expr.match(data)
            if match:
                return match.groupdict()

        return {}

    def _match_many(self, expr, data):
        result = []
        pos = 0
        while True:
            match = expr.match(data, pos)
            if match:
                result.append(match.groupdict())
                pos = match.endpos
            else:
                break

        return result

    def _evaluate(self, token):
        if isinstance(token, (CommentStmt, UnknownStmt, EofStmt)):
            return

        elif isinstance(token, ParamStmt):
            self._evaluate_param(token)

        elif isinstance(token, CoordStmt):
            self._evaluate_coord(token)

        elif isinstance(token, ApertureStmt):
            self._evaluate_aperture(token)

        else:
            raise Exception("Invalid token to evaluate")

    def _evaluate_param(self, param):
        if param.type == "FS":
            self.ctx.set_coord_format(param.zero, param.x, param.y)
            self.ctx.set_coord_notation(param.notation)

    def _evaluate_coord(self, coord):
        self.ctx.move(coord.x, coord.y)

    def _evaluate_aperture(self, aperture):
        self.ctx.aperture(aperture.d)


if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        print f
        g = Gerber()
        g.parse(f)
