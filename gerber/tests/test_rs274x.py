#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
import os

from ..rs274x import read, GerberFile
from .tests import *


TOP_COPPER_FILE = os.path.join(os.path.dirname(__file__),
                               'resources/top_copper.GTL')

MULTILINE_READ_FILE = os.path.join(os.path.dirname(__file__),
                                   'resources/multiline_read.ger')


def test_read():
    top_copper = read(TOP_COPPER_FILE)
    assert(isinstance(top_copper, GerberFile))


def test_multiline_read():
    multiline = read(MULTILINE_READ_FILE)
    assert(isinstance(multiline, GerberFile))
    assert_equal(10, len(multiline.statements))


def test_comments_parameter():
    top_copper = read(TOP_COPPER_FILE)
    assert_equal(top_copper.comments[0], 'This is a comment,:')


def test_size_parameter():
    top_copper = read(TOP_COPPER_FILE)
    size = top_copper.size
    assert_almost_equal(size[0], 2.256900, 6)
    assert_almost_equal(size[1], 1.500000, 6)


def test_conversion():
    top_copper = read(TOP_COPPER_FILE)
    assert_equal(top_copper.units, 'inch')
    top_copper_inch = read(TOP_COPPER_FILE)
    top_copper.to_metric()
    for statement in top_copper_inch.statements:
        statement.to_metric()
    for primitive in top_copper_inch.primitives:
        primitive.to_metric()
    assert_equal(top_copper.units, 'metric')
    for i, m in zip(top_copper.statements, top_copper_inch.statements):
        assert_equal(i, m)

    for i, m in zip(top_copper.primitives, top_copper_inch.primitives):
        assert_equal(i, m)
