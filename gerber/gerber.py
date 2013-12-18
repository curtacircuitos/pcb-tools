#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import string


def red(s):
    return '\033[1;31m{0}\033[0;m'.format(s)


class Statement:
    def __init__(self):
        pass


class ParamStmt(Statement):
    def __init__(self):
        pass


class CoordStmt(Statement):
    def __init__(self):
        pass


class ApertureStmt(Statement):
    def __init__(self):
        pass


class CommentStmt(Statement):
    def __init__(self, comment):
        self.comment = comment


class EofStmt(Statement):
    pass


class UnknownStmt(Statement):
    def __init__(self, line):
        self.line = line


class Gerber:
    NUMBER = r"[\+-]?\d+"
    FUNCTION = r"G\d{2}"
    STRING = r"[a-zA-Z0-9_+\-/!?<>”’(){}.\|&@# :]+"

    COORD_OP = r"D[0]?[123]"

    PARAM_STMT = re.compile(r"%.*%")

    COORD_STMT = re.compile((
        r"(?P<f>{f})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, f=FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(G54)?D\d+\*")

    COMMENT_STMT = re.compile(r"G04(?P<comment>{string})(\*)?".format(string=STRING))

    EOF_STMT = re.compile(r"M02\*")

    def __init__(self):
        self.tokens = []

    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        self.tokens = list(self.tokenize(data))

        for token in self.tokens:
            if isinstance(token, UnknownStmt):
                print filename
                print red("[INVALID TOKEN]")
                print "'%s'" % token.line

    def _match_one(self, expr, data):
        match = expr.match(data)
        if match is None:
            return {}
        else:
            return match.groupdict()

    def _match_many(self, expr, data):
        matches = expr.finditer(data)
        if not matches:
            return []
        else:
            return [match.groupdict() for match in matches]

    def tokenize(self, data):
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

            # parameter
            param = self._match_one(self.PARAM_STMT, line)
            if param:
                yield ParamStmt()
                continue

            # coord
            coords = self._match_many(self.COORD_STMT, line)
            if coords:
                for coord in coords:
                    yield CoordStmt()
                continue

            # aperture selection
            aperture = self._match_one(self.APERTURE_STMT, line)
            if aperture:
                yield ApertureStmt()
                continue

            # comment
            comment = self._match_one(self.COMMENT_STMT, line)
            if comment:
                yield CommentStmt(comment["comment"])
                continue

            # eof
            eof = self._match_one(self.EOF_STMT, line)
            if eof:
                yield EofStmt()
                continue

            yield UnknownStmt(line)

if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        g = Gerber()
        g.parse(f)
