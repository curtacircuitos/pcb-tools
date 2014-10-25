#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import json


class Statement(object):
    def __init__(self, type):
        self.type = type

    def __str__(self):
        s = "<{0} ".format(self.__class__.__name__)

        for key, value in self.__dict__.items():
            s += "{0}={1} ".format(key, value)

        s = s.rstrip() + ">"
        return s


class ParamStmt(Statement):
    def __init__(self, param):
        Statement.__init__(self, "PARAM")
        self.param = param



class FSParamStmt(ParamStmt):
    def __init__(self, param, zero="L", notation="A", x="24", y="24"):
        ParamStmt.__init__(self, param)
        self.zero = zero
        self.notation = notation
        self.x = x
        self.y = y

    def to_gerber(self):
        return '%FS{0}{1}X{2}Y{3}*%'.format(self.zero, self.notation,
                                            self.x, self.y)

class MOParamStmt(ParamStmt):
    def __init__(self, param, mo):
        ParamStmt.__init__(self, param)
        self.mo = mo

    def to_gerber(self):
        return '%MO{0}*%'.format(self.mo)

class IPParamStmt(ParamStmt):
    def __init__(self, param, ip):
        ParamStmt.__init__(self, param)
        self.ip = ip

    def to_gerber(self):
        return '%IP{0}*%'.format(self.ip)


class OFParamStmt(ParamStmt):
    def __init__(self, param, a, b):
        ParamStmt.__init__(self, param)
        self.a = a
        self.b = b

    def to_gerber(self):
        ret = '%OF'
        if self.a:
            ret += 'A' + self.a
        if self.b:
            ret += 'B' + self.b
        return ret + '*%'


class LPParamStmt(ParamStmt):
    def __init__(self, param, lp):
        ParamStmt.__init__(self, param)
        self.lp = lp

    def to_gerber(self):
        return '%LP{0}*%'.format(self.lp)


class ADParamStmt(ParamStmt):
    def __init__(self, param, d, shape, modifiers):
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

class AMParamStmt(ParamStmt):
    def __init__(self, param, name, macro):
        ParamStmt.__init__(self, param)
        self.name = name
        self.macro = macro

    def to_gerber(self):
        #think this is right...
        return '%AM{0}*{1}*%'.format(self.name, self.macro)

class INParamStmt(ParamStmt):
    def __init__(self, param, name):
        ParamStmt.__init__(self, param)
        self.name = name

    def to_gerber(self):
        return '%IN{0}*%'.format(self.name)


class LNParamStmt(ParamStmt):
    def __init__(self, param, name):
        ParamStmt.__init__(self, param)
        self.name = name

    def to_gerber(self):
        return '%LN{0}*%'.format(self.name)

class CoordStmt(Statement):
    def __init__(self, function, x, y, i, j, op):
        Statement.__init__(self, "COORD")
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
        if self.x:
            ret += 'X{0}'.format(self.x)
        if self.y:
            ret += 'Y{0}'.format(self.y)
        if self.i:
            ret += 'I{0}'.format(self.i)
        if self.j:
            ret += 'J{0}'.format(self.j)
        if self.op:
            ret += self.op
        return ret + '*'


class ApertureStmt(Statement):
    def __init__(self, d):
        Statement.__init__(self, "APERTURE")
        self.d = int(d)

    def to_gerber(self):
        return 'G54D{0}*'.format(self.d)

class CommentStmt(Statement):
    def __init__(self, comment):
        Statement.__init__(self, "COMMENT")
        self.comment = comment

    def to_gerber(self):
        return 'G04{0}*'.format(self.comment)

class EofStmt(Statement):
    def __init__(self):
        Statement.__init__(self, "EOF")

    def to_gerber(self):
        return 'M02*'

class UnknownStmt(Statement):
    def __init__(self, line):
        Statement.__init__(self, "UNKNOWN")
        self.line = line


class GerberParser(object):
    NUMBER = r"[\+-]?\d+"
    DECIMAL = r"[\+-]?\d+([.]?\d+)?"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"
    NAME = r"[a-zA-Z_$][a-zA-Z_$0-9]+"
    FUNCTION = r"G\d{2}"

    COORD_OP = r"D[0]?[123]"

    FS = r"(?P<param>FS)(?P<zero>(L|T))?(?P<notation>(A|I))X(?P<x>[0-7][0-7])Y(?P<y>[0-7][0-7])"
    MO = r"(?P<param>MO)(?P<mo>(MM|IN))"
    IP = r"(?P<param>IP)(?P<ip>(POS|NEG))"
    LP = r"(?P<param>LP)(?P<lp>(D|C))"
    AD_CIRCLE = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>C)[,](?P<modifiers>[^,]*)"
    AD_RECT = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>R)[,]?(?P<modifiers>[^,]+)?"
    AD_OBROUND = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>O)[,](?P<modifiers>[^,]*)"
    AD_POLY = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>P)[,](?P<modifiers>[^,]*)"
    AD_MACRO = r"(?P<param>AD)D(?P<d>\d+)(?P<shape>{name})[,]?(?P<modifiers>[^,]+)?".format(name=NAME)
    AM = r"(?P<param>AM)(?P<name>{name})\*(?P<macro>.*)".format(name=NAME)

    # begin deprecated
    OF = r"(?P<param>OF)(A(?P<a>{decimal}))?(B(?P<b>{decimal}))?".format(decimal=DECIMAL)
    IN = r"(?P<param>IN)(?P<name>.*)"
    LN = r"(?P<param>LN)(?P<name>.*)"
    # end deprecated

    PARAMS = (FS, MO, IP, LP, AD_CIRCLE, AD_RECT, AD_OBROUND, AD_POLY, AD_MACRO, AM, OF, IN, LN)
    PARAM_STMT = [re.compile(r"%{0}\*%".format(p)) for p in PARAMS]

    COORD_STMT = re.compile((
        r"(?P<function>{function})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, function=FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(G54)?D(?P<d>\d+)\*")

    #COMMENT_STMT = re.compile(r"G04(?P<comment>{string})(\*)?".format(string=STRING))
    #spec is unclear on whether all chars allowed in comment string -
    #seems reasonable to be more permissive.
    COMMENT_STMT = re.compile(r"G04(?P<comment>[^*]*)(\*)?")

    EOF_STMT = re.compile(r"(?P<eof>M02)\*")

    def __init__(self, ctx=None):
        self.statements = []
        self.ctx = ctx

    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        for stmt in self._parse(data):
            self.statements.append(stmt)
            if self.ctx:
                self.ctx.evaluate(stmt)

    def dump_json(self):
        stmts = {"statements": [stmt.__dict__ for stmt in self.statements]}
        return json.dumps(stmts)

    def dump_str(self):
        s = ""
        for stmt in self.statements:
            s += str(stmt) + "\n"
        return s

    def dump(self):
        self.ctx.dump()

    def _parse(self, data):
        oldline = ''

        for i, line in enumerate(data):
            line = oldline + line.strip()

            # skip empty lines
            if not len(line):
                continue

            # deal with multi-line parameters
            if line.startswith("%") and not line.endswith("%"):
                oldline = line
                continue

            did_something = True # make sure we do at least one loop
            while did_something and len(line) > 0:
                did_something = False
                # coord
                (coord, r) = self._match_one(self.COORD_STMT, line)
                if coord:
                    yield CoordStmt(**coord)
                    line = r
                    did_something = True
                    continue

                # aperture selection
                (aperture, r) = self._match_one(self.APERTURE_STMT, line)
                if aperture:
                    yield ApertureStmt(**aperture)

                    did_something = True
                    line = r
                    continue

                # comment
                (comment, r) = self._match_one(self.COMMENT_STMT, line)
                if comment:
                    yield CommentStmt(comment["comment"])
                    did_something = True
                    line = r
                    continue

                # parameter
                (param, r) = self._match_one_from_many(self.PARAM_STMT, line)
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
                    did_something = True
                    line = r
                    continue

                # eof
                (eof, r) = self._match_one(self.EOF_STMT, line)
                if eof:
                    yield EofStmt()
                    did_something = True
                    line = r
                    continue

                if False:
                    print self.COORD_STMT.pattern
                    print self.APERTURE_STMT.pattern
                    print self.COMMENT_STMT.pattern
                    print self.EOF_STMT.pattern
                    for i in self.PARAM_STMT:
                        print i.pattern

                if line.find('*') > 0:
                    yield UnknownStmt(line)
                    did_something = True
                    line = ""
                    continue

            oldline = line

    def _match_one(self, expr, data):
        match = expr.match(data)
        if match is None:
            return ({}, None)
        else:
            return (match.groupdict(), data[match.end(0):])

    def _match_one_from_many(self, exprs, data):
        for expr in exprs:
            match = expr.match(data)
            if match:
                return (match.groupdict(), data[match.end(0):])

        return ({}, None)
