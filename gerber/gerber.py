#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json


def red(s):
    return '\033[1;31m{0}\033[0;m'.format(s)


class Statement:
    def __init__(self, type):
        self.type = type


class ParamStmt(Statement):
    def __init__(self, param):
        Statement.__init__(self, "PARAM")
        self.param = param


class FSParamStmt(ParamStmt):
    def __init__(self, param, zero, notation, x, y):
        ParamStmt.__init__(self, param)
        self.zero = zero
        self.notation = notation
        self.x = x
        self.y = y


class MOParamStmt(ParamStmt):
    def __init__(self, param, mo):
        ParamStmt.__init__(self, param)
        self.mo = mo


class IPParamStmt(ParamStmt):
    def __init__(self, param, ip):
        ParamStmt.__init__(self, param)
        self.ip = ip


class OFParamStmt(ParamStmt):
    def __init__(self, param, a, b):
        ParamStmt.__init__(self, param)
        self.a = a
        self.b = b


class LPParamStmt(ParamStmt):
    def __init__(self, param, lp):
        ParamStmt.__init__(self, param)
        self.lp = lp


class ADParamStmt(ParamStmt):
    def __init__(self, param, d, aperture, modifiers):
        ParamStmt.__init__(self, param)
        self.d = d
        self.aperture = aperture
        self.modifiers = [[x for x in m.split("X")] for m in modifiers.split(",")]


class AMParamStmt(ParamStmt):
    def __init__(self, param, name, macro):
        ParamStmt.__init__(self, param)
        self.name = name
        self.macro = macro


class INParamStmt(ParamStmt):
    def __init__(self, param, name):
        ParamStmt.__init__(self, param)
        self.name = name


class LNParamStmt(ParamStmt):
    def __init__(self, param, name):
        ParamStmt.__init__(self, param)
        self.name = name


class CoordStmt(Statement):
    def __init__(self, function, x, y, i, j, op):
        Statement.__init__(self, "COORD")
        self.function = function
        self.x = x
        self.y = y
        self.i = i
        self.j = j
        self.op = op


class ApertureStmt(Statement):
    def __init__(self, d):
        Statement.__init__(self, "APERTURE")
        self.d = int(d)


class CommentStmt(Statement):
    def __init__(self, comment):
        Statement.__init__(self, "COMMENT")
        self.comment = comment


class EofStmt(Statement):
    def __init__(self):
        Statement.__init__(self, "EOF")


class UnknownStmt(Statement):
    def __init__(self, line):
        Statement.__init__(self, "UNKNOWN")
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
    DECIMAL = r"[\+-]?\d+([.]?\d+)?"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"
    NAME = "[a-zA-Z_$][a-zA-Z_$0-9]+"
    FUNCTION = r"G\d{2}"

    COORD_OP = r"D[0]?[123]"

    FS = r"(?P<param>FS)(?P<zero>(L|T))(?P<notation>(A|I))X(?P<x>[0-7][0-7])Y(?P<y>[0-7][0-7])"
    MO = r"(?P<param>MO)(?P<mo>(MM|IN))"
    IP = r"(?P<param>IP)(?P<ip>(POS|NEG))"
    LP = r"(?P<param>LP)(?P<lp>(D|C))"
    AD_CIRCLE = r"(?P<param>AD)D(?P<d>\d+)(?P<aperture>C)[,](?P<modifiers>[^,]*)"
    AD_RECT = r"(?P<param>AD)D(?P<d>\d+)(?P<aperture>R)[,](?P<modifiers>[^,]*)"
    AD_OBROUND = r"(?P<param>AD)D(?P<d>\d+)(?P<aperture>O)[,](?P<modifiers>[^,]*)"
    AD_POLY = r"(?P<param>AD)D(?P<d>\d+)(?P<aperture>P)[,](?P<modifiers>[^,]*)"
    AD_MACRO = r"(?P<param>AD)D(?P<d>\d+)+(?P<aperture>{name})[,](?P<modifiers>[^,]*)".format(name=NAME)
    AM = r"(?P<param>AM)(?P<name>{name})\*(?P<macro>.*)".format(name=NAME)

    # begin deprecated
    OF = r"(?P<param>OF)(A(?P<a>{decimal}))?(B(?P<b>{decimal}))?".format(decimal=DECIMAL)
    IN = r"(?P<param>IN)(?P<name>.*)"
    LN = r"(?P<param>LN)(?P<name>.*)"
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
        self.statements = []
        self.ctx = GerberContext()

    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        for stmt in self._parse(data):
            self.statements.append(stmt)
            self._evaluate(stmt)

    def dump(self):
        stmts = {"statements": [stmt.__dict__ for stmt in self.statements]}
        return json.dumps(stmts)

    def _parse(self, data):
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
                if param["param"] == "FS":
                    yield FSParamStmt(**param)
                elif param["param"] == "MO":
                    yield MOParamStmt(**param)
                elif param["param"] == "IP":
                    yield IPParamStmt(**param)
                elif param["param"] == "LP":
                    yield LPParamStmt(**param)
                elif param["param"] == "AD":
                    yield ADParamStmt(**param)
                elif param["param"] == "AM":
                    yield AMParamStmt(**param)
                elif param["param"] == "OF":
                    yield OFParamStmt(**param)
                elif param["param"] == "IN":
                    yield INParamStmt(**param)
                elif param["param"] == "LN":
                    yield LNParamStmt(**param)
                else:
                    yield UnknownStmt(line)

                continue

            # eof
            eof = self._match_one(self.EOF_STMT, line)
            if eof:
                yield EofStmt()
                continue

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

    def _evaluate(self, stmt):
        if isinstance(stmt, (CommentStmt, UnknownStmt, EofStmt)):
            return

        elif isinstance(stmt, ParamStmt):
            self._evaluate_param(stmt)

        elif isinstance(stmt, CoordStmt):
            self._evaluate_coord(stmt)

        elif isinstance(stmt, ApertureStmt):
            self._evaluate_aperture(stmt)

        else:
            raise Exception("Invalid statement to evaluate")

    def _evaluate_param(self, stmt):
        if stmt.param == "FS":
            self.ctx.set_coord_format(stmt.zero, stmt.x, stmt.y)
            self.ctx.set_coord_notation(stmt.notation)

    def _evaluate_coord(self, stmt):
        self.ctx.move(stmt.x, stmt.y)

    def _evaluate_aperture(self, stmt):
        self.ctx.aperture(stmt.d)


if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        g = Gerber()
        g.parse(f)
        print g.dump()
