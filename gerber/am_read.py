#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
# copyright 2014 Paulo Henrique Silva <ph.silva@gmail.com>
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
""" This module provides RS-274-X AM macro modifiers parsing.
"""

from .am_eval import OpCode, eval_macro

import string


class Token:
    ADD = "+"
    SUB = "-"
    # compatibility as many gerber writes do use non compliant X
    MULT = ("x", "X")
    DIV = "/"
    OPERATORS = (ADD, SUB, MULT[0], MULT[1], DIV)
    LEFT_PARENS = "("
    RIGHT_PARENS = ")"
    EQUALS = "="
    EOF = "EOF"


def token_to_opcode(token):
    if token == Token.ADD:
        return OpCode.ADD
    elif token == Token.SUB:
        return OpCode.SUB
    elif token in Token.MULT:
        return OpCode.MUL
    elif token == Token.DIV:
        return OpCode.DIV
    else:
        return None


def precedence(token):
    if token == Token.ADD or token == Token.SUB:
        return 1
    elif token in Token.MULT or token == Token.DIV:
        return 2
    else:
        return 0


def is_op(token):
    return token in Token.OPERATORS


class Scanner:

    def __init__(self, s):
        self.buff = s
        self.n = 0

    def eof(self):
        return self.n == len(self.buff)

    def peek(self):
        if not self.eof():
            return self.buff[self.n]

        return Token.EOF

    def ungetc(self):
        if self.n > 0:
            self.n -= 1

    def getc(self):
        if self.eof():
            return ""

        c = self.buff[self.n]
        self.n += 1
        return c

    def readint(self):
        n = ""
        while not self.eof() and (self.peek() in string.digits):
            n += self.getc()
        return int(n)

    def readfloat(self):
        n = ""
        while not self.eof() and (self.peek() in string.digits or self.peek() == "."):
            n += self.getc()
        # weird case where zero is ommited inthe last modifider, like in ',0.'
        if n == ".":
            return 0
        return float(n)

    def readstr(self, end="*"):
        s = ""
        while not self.eof() and self.peek() != end:
            s += self.getc()
        return s.strip()


def print_instructions(instructions):
    for opcode, argument in instructions:
        print("%s %s" % (OpCode.str(opcode),
                         str(argument) if argument is not None else ""))


def read_macro(macro):
    instructions = []

    for block in macro.split("*"):

        is_primitive = False
        is_equation = False

        found_equation_left_side = False
        found_primitive_code = False

        equation_left_side = 0
        primitive_code = 0

        unary_minus_allowed = False
        unary_minus = False

        if Token.EQUALS in block:
            is_equation = True
        else:
            is_primitive = True

        scanner = Scanner(block)

        # inlined here for compactness and convenience
        op_stack = []

        def pop():
            return op_stack.pop()

        def push(op):
            op_stack.append(op)

        def top():
            return op_stack[-1]

        def empty():
            return len(op_stack) == 0

        while not scanner.eof():

            c = scanner.getc()

            if c == ",":
                found_primitive_code = True

                # add all instructions on the stack to finish last modifier
                while not empty():
                    instructions.append((token_to_opcode(pop()), None))

                unary_minus_allowed = True

            elif c in Token.OPERATORS:
                if c == Token.SUB and unary_minus_allowed:
                    unary_minus = True
                    unary_minus_allowed = False
                    continue

                while not empty() and is_op(top()) and precedence(top()) >= precedence(c):
                    instructions.append((token_to_opcode(pop()), None))

                push(c)

            elif c == Token.LEFT_PARENS:
                push(c)

            elif c == Token.RIGHT_PARENS:
                while not empty() and top() != Token.LEFT_PARENS:
                    instructions.append((token_to_opcode(pop()), None))

                if empty():
                    raise ValueError("unbalanced parentheses")

                # discard "("
                pop()

            elif c.startswith("$"):
                n = scanner.readint()

                if is_equation and not found_equation_left_side:
                    equation_left_side = n
                else:
                    instructions.append((OpCode.LOAD, n))

            elif c == Token.EQUALS:
                found_equation_left_side = True

            elif c == "0":
                if is_primitive and not found_primitive_code:
                    instructions.append((OpCode.PUSH, scanner.readstr("*")))
                    found_primitive_code = True
                else:
                    # decimal or integer disambiguation
                    if scanner.peek() not in '.' or scanner.peek() == Token.EOF:
                        instructions.append((OpCode.PUSH, 0))

            elif c in "123456789.":
                scanner.ungetc()

                if is_primitive and not found_primitive_code:
                    primitive_code = scanner.readint()
                else:
                    n = scanner.readfloat()
                    if unary_minus:
                        unary_minus = False
                        n *= -1

                    instructions.append((OpCode.PUSH, n))
            else:
                # whitespace or unknown char
                pass

        # add all instructions on the stack to finish last modifier (if any)
        while not empty():
            instructions.append((token_to_opcode(pop()), None))

        # at end, we either have a primitive or a equation
        if is_primitive and found_primitive_code:
            instructions.append((OpCode.PRIM, primitive_code))

        if is_equation:
            instructions.append((OpCode.STORE, equation_left_side))

    return instructions

if __name__ == '__main__':
    import sys

    instructions = read_macro(sys.argv[1])

    print("insructions:")
    print_instructions(instructions)

    print("eval:")
    for primitive in eval_macro(instructions):
        print(primitive)
