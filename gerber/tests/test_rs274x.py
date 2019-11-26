#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
import os
import pytest

from ..rs274x import read, GerberFile


TOP_COPPER_FILE = os.path.join(os.path.dirname(__file__), "resources/top_copper.GTL")

MULTILINE_READ_FILE = os.path.join(
    os.path.dirname(__file__), "resources/multiline_read.ger"
)


def test_read():
    top_copper = read(TOP_COPPER_FILE)
    assert isinstance(top_copper, GerberFile)


def test_multiline_read():
    multiline = read(MULTILINE_READ_FILE)
    assert isinstance(multiline, GerberFile)
    assert 10 == len(multiline.statements)


def test_comments_parameter():
    top_copper = read(TOP_COPPER_FILE)
    assert top_copper.comments[0] == "This is a comment,:"


def test_size_parameter():
    top_copper = read(TOP_COPPER_FILE)
    size = top_copper.size
    pytest.approx(size[0], 2.256900, 6)
    pytest.approx(size[1], 1.500000, 6)


def test_conversion():
    top_copper = read(TOP_COPPER_FILE)
    assert top_copper.units == "inch"
    top_copper_inch = read(TOP_COPPER_FILE)
    top_copper.to_metric()
    for statement in top_copper_inch.statements:
        statement.to_metric()
    for primitive in top_copper_inch.primitives:
        primitive.to_metric()
    assert top_copper.units == "metric"
    for i, m in zip(top_copper.statements, top_copper_inch.statements):
        assert i == m

    for i, m in zip(top_copper.primitives, top_copper_inch.primitives):
        assert i == m
