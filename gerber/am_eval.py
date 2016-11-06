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
""" This module provides RS-274-X AM macro evaluation.
"""


class OpCode:
    PUSH = 1
    LOAD = 2
    STORE = 3
    ADD = 4
    SUB = 5
    MUL = 6
    DIV = 7
    PRIM = 8

    @staticmethod
    def str(opcode):
        if opcode == OpCode.PUSH:
            return "OPCODE_PUSH"
        elif opcode == OpCode.LOAD:
            return "OPCODE_LOAD"
        elif opcode == OpCode.STORE:
            return "OPCODE_STORE"
        elif opcode == OpCode.ADD:
            return "OPCODE_ADD"
        elif opcode == OpCode.SUB:
            return "OPCODE_SUB"
        elif opcode == OpCode.MUL:
            return "OPCODE_MUL"
        elif opcode == OpCode.DIV:
            return "OPCODE_DIV"
        elif opcode == OpCode.PRIM:
            return "OPCODE_PRIM"
        else:
            return "UNKNOWN"


def eval_macro(instructions, parameters={}):

    if not isinstance(parameters, type({})):
        p = {}
        for i, val in enumerate(parameters):
            p[i + 1] = val

        parameters = p

    stack = []

    def pop():
        return stack.pop()

    def push(op):
        stack.append(op)

    def top():
        return stack[-1]

    def empty():
        return len(stack) == 0

    for opcode, argument in instructions:
        if opcode == OpCode.PUSH:
            push(argument)

        elif opcode == OpCode.LOAD:
            push(parameters.get(argument, 0))

        elif opcode == OpCode.STORE:
            parameters[argument] = pop()

        elif opcode == OpCode.ADD:
            op1 = pop()
            op2 = pop()
            push(op2 + op1)

        elif opcode == OpCode.SUB:
            op1 = pop()
            op2 = pop()
            push(op2 - op2)

        elif opcode == OpCode.MUL:
            op1 = pop()
            op2 = pop()
            push(op2 * op1)

        elif opcode == OpCode.DIV:
            op1 = pop()
            op2 = pop()
            push(op2 / op1)

        elif opcode == OpCode.PRIM:
            yield "%d,%s" % (argument, ",".join([str(x) for x in stack]))
            stack = []
