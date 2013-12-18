#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


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


class UnexpectedStmt(Statement):
    def __init__(self, line):
        self.line = line


class Gerber:
    NUMBER = r"[\+-]?\d+"
    FUNCTION = r"G\d{2}"
    STRING = r"[a-zA-Z0-9_+-/!?<>”’(){}.\|&@# :]+"

    COORD_OP = r"D[0]?[123]"

    PARAM_STMT = re.compile(r"%.*%")

    COORD_STMT = re.compile((
        r"(?P<f>{f})?"
        r"(X(?P<x>{number}))?(Y(?P<y>{number}))?"
        r"(I(?P<i>{number}))?(J(?P<j>{number}))?"
        r"(?P<op>{op})?\*".format(number=NUMBER, f=FUNCTION, op=COORD_OP)))

    APERTURE_STMT = re.compile(r"(G54)?D\d+\*")

    COMMENT_STMT = re.compile(r"G04(?P<comment>{string})\*".format(string=STRING))

    EOF_STMT = re.compile(r"M02\*")

    def __init__(self):
        self.tokens = []

    def parse(self, filename):
        fp = open(filename, "r")
        data = fp.readlines()

        self.tokens = list(self.tokenize(data))

        for token in self.tokens:
            if isinstance(token, UnexpectedStmt):
                print red("[UNEXPECTED TOKEN]")
                print token.line

    def tokenize(self, data):
        multiline = None

        for i, line in enumerate(data):
            # remove EOL
            if multiline:    
                line = multiline + line.strip()
            else:
                line = line.strip()

            # deal with multi-line parameters
            if line.startswith("%") and not line.endswith("%"):
                multiline = line
                continue
            else:
                multiline = None

            # parameter
            match = self.PARAM_STMT.match(line)
            if match:
                yield ParamStmt()
                continue

            # coord
            matches = self.COORD_STMT.finditer(line)
            if matches:
                for match in matches:
                    yield CoordStmt()
                continue

            # aperture selection
            match = self.APERTURE_STMT.match(line)
            if match:
                yield ApertureStmt()
                continue

            # comment
            match = self.COMMENT_STMT.match(line)
            if match:
                yield CommentStmt(match.groupdict("comment"))
                continue

            # eof
            match = self.EOF_STMT.match(line)
            if match:
                yield EofStmt()
                continue

            yield UnexpectedStmt(line)

if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        g = Gerber()
        g.parse(f)
