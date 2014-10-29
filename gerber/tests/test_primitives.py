#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..primitives import *
from tests import *



def test_line_angle():
    """ Test Line primitive angle calculation
    """
    cases = [((0, 0), (1, 0), math.radians(0)),
             ((0, 0), (1, 1), math.radians(45)),
             ((0, 0), (0, 1), math.radians(90)),
             ((0, 0), (-1, 1), math.radians(135)),
             ((0, 0), (-1, 0), math.radians(180)),
             ((0, 0), (-1, -1), math.radians(225)),
             ((0, 0), (0, -1), math.radians(270)),
             ((0, 0), (1, -1), math.radians(315)),]
    for start, end, expected in cases:
        l = Line(start, end, 0)
        line_angle = (l.angle + 2 * math.pi) % (2 * math.pi)
        assert_almost_equal(line_angle, expected)
    
def test_line_bounds():
    """ Test Line primitive bounding box calculation
    """
    cases = [((0, 0), (1, 1), ((0, 1), (0, 1))),
             ((-1, -1), (1, 1), ((-1, 1), (-1, 1))),
             ((1, 1), (-1, -1), ((-1, 1), (-1, 1))),
             ((-1, 1), (1, -1), ((-1, 1), (-1, 1))),]
    for start, end, expected in cases:
        l = Line(start, end, 0)
        assert_equal(l.bounding_box, expected)

def test_arc_radius():
    """ Test Arc primitive radius calculation
    """
    cases = [((-3, 4), (5, 0), (0, 0), 5),
            ((0, 1), (1, 0), (0, 0), 1),]

    for start, end, center, radius in cases:
        a = Arc(start, end, center, 'clockwise', 0)
        assert_equal(a.radius, radius)


def test_arc_sweep_angle():
    """ Test Arc primitive sweep angle calculation
    """
    cases = [((1, 0), (0, 1), (0, 0), 'counterclockwise', math.radians(90)),
             ((1, 0), (0, 1), (0, 0), 'clockwise', math.radians(270)),
             ((1, 0), (-1, 0), (0, 0), 'clockwise', math.radians(180)),
             ((1, 0), (-1, 0), (0, 0), 'counterclockwise', math.radians(180)),]

    for start, end, center, direction, sweep in cases:
        a = Arc(start, end, center, direction, 0)
        assert_equal(a.sweep_angle, sweep)


def test_arc_bounds():
    """ Test Arc primitive bounding box calculation
    """
    cases = [((1, 0), (0, 1), (0, 0), 'clockwise',  ((-1, 1), (-1, 1))),
             ((1, 0), (0, 1), (0, 0), 'counterclockwise',  ((0, 1), (0, 1))),
             #TODO: ADD MORE TEST CASES HERE
             ]
    
    for start, end, center, direction, bounds in cases:
        a = Arc(start, end, center, direction, 0)
        assert_equal(a.bounding_box, bounds)
    
def test_circle_radius():
    """ Test Circle primitive radius calculation
    """
    c = Circle((1, 1), 2)
    assert_equal(c.radius, 1)
    
def test_circle_bounds():
    """ Test Circle bounding box calculation
    """
    c = Circle((1, 1), 2)
    assert_equal(c.bounding_box, ((0, 2), (0, 2)))
    
    
