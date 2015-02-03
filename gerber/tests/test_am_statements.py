#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import *
from ..am_statements import *

def test_AMPrimitive_ctor():
    for exposure in ('on', 'off', 'ON', 'OFF'):
        for code in (0, 1, 2, 4, 5, 6, 7, 20, 21, 22):
            p = AMPrimitive(code, exposure)
            assert_equal(p.code, code)
            assert_equal(p.exposure, exposure.lower())


def test_AMPrimitive_validation():
    assert_raises(TypeError, AMPrimitive, '1', 'off')
    assert_raises(ValueError, AMPrimitive, 0, 'exposed')
    assert_raises(ValueError, AMPrimitive, 3, 'off')


def test_AMCommentPrimitive_ctor():
    c = AMCommentPrimitive(0, ' This is a comment *')
    assert_equal(c.code, 0)
    assert_equal(c.comment, 'This is a comment')


def test_AMCommentPrimitive_validation():
    assert_raises(ValueError, AMCommentPrimitive, 1, 'This is a comment')


def test_AMCommentPrimitive_factory():
    c = AMCommentPrimitive.from_gerber('0 Rectangle with rounded corners. *')
    assert_equal(c.code, 0)
    assert_equal(c.comment, 'Rectangle with rounded corners.')


def test_AMCommentPrimitive_dump():
    c = AMCommentPrimitive(0, 'Rectangle with rounded corners.')
    assert_equal(c.to_gerber(), '0 Rectangle with rounded corners. *')


def test_AMCirclePrimitive_ctor():
    test_cases = ((1, 'on', 0, (0, 0)),
                  (1, 'off', 1, (0, 1)),
                  (1, 'on', 2.5, (0, 2)),
                  (1, 'off', 5.0, (3, 3)))
    for code, exposure, diameter, position in test_cases:
        c = AMCirclePrimitive(code, exposure, diameter, position)
        assert_equal(c.code, code)
        assert_equal(c.exposure, exposure)
        assert_equal(c.diameter, diameter)
        assert_equal(c.position, position)


def test_AMCirclePrimitive_validation():
    assert_raises(ValueError, AMCirclePrimitive, 2, 'on', 0, (0, 0))


def test_AMCirclePrimitive_factory():
    c = AMCirclePrimitive.from_gerber('1,0,5,0,0*')
    assert_equal(c.code, 1)
    assert_equal(c.exposure, 'off')
    assert_equal(c.diameter, 5)
    assert_equal(c.position, (0,0))


def test_AMCirclePrimitive_dump():
    c = AMCirclePrimitive(1, 'off', 5, (0, 0))
    assert_equal(c.to_gerber(), '1,0,5,0,0*')
    c = AMCirclePrimitive(1, 'on', 5, (0, 0))
    assert_equal(c.to_gerber(), '1,1,5,0,0*')



    