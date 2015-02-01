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


def test_ellipse_ctor():
    """ Test ellipse creation
    """
    e = Ellipse((2, 2), 3, 2)
    assert_equal(e.position, (2, 2))
    assert_equal(e.width, 3)
    assert_equal(e.height, 2)


def test_ellipse_bounds():
    """ Test ellipse bounding box calculation
    """
    e = Ellipse((2, 2), 4, 2)
    assert_equal(e.bounding_box, ((0, 4), (1, 3)))
    e = Ellipse((2, 2), 4, 2, rotation=90)
    assert_equal(e.bounding_box, ((1, 3), (0, 4)))
    e = Ellipse((2, 2), 4, 2, rotation=180)
    assert_equal(e.bounding_box, ((0, 4), (1, 3)))
    e = Ellipse((2, 2), 4, 2, rotation=270)
    assert_equal(e.bounding_box, ((1, 3), (0, 4)))

def test_rectangle_ctor():
    """ Test rectangle creation
    """
    test_cases = (((0,0), 1, 1), ((0, 0), 1, 2), ((1,1), 1, 2))
    for pos, width, height in test_cases:
        r = Rectangle(pos, width, height)
        assert_equal(r.position, pos)
        assert_equal(r.width, width)
        assert_equal(r.height, height)

def test_rectangle_bounds():
    """ Test rectangle bounding box calculation
    """
    r = Rectangle((0,0), 2, 2)
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))
    r = Rectangle((0,0), 2, 2, rotation=45)
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (-math.sqrt(2), math.sqrt(2)))
    assert_array_almost_equal(ybounds, (-math.sqrt(2), math.sqrt(2)))
    
def test_diamond_ctor():
    """ Test diamond creation
    """
    test_cases = (((0,0), 1, 1), ((0, 0), 1, 2), ((1,1), 1, 2))
    for pos, width, height in test_cases:
        d = Diamond(pos, width, height)
        assert_equal(d.position, pos)
        assert_equal(d.width, width)
        assert_equal(d.height, height)

def test_diamond_bounds():
    """ Test diamond bounding box calculation
    """
    d = Diamond((0,0), 2, 2)
    xbounds, ybounds = d.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))
    d = Diamond((0,0), math.sqrt(2), math.sqrt(2), rotation=45)
    xbounds, ybounds = d.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))


def test_chamfer_rectangle_ctor():
    """ Test chamfer rectangle creation
    """
    test_cases = (((0,0), 1, 1, 0.2, (True, True, False, False)),
                  ((0, 0), 1, 2, 0.3, (True, True, True, True)),
                  ((1,1), 1, 2, 0.4, (False, False, False, False)))
    for pos, width, height, chamfer, corners in test_cases:
        r = ChamferRectangle(pos, width, height, chamfer, corners)
        assert_equal(r.position, pos)
        assert_equal(r.width, width)
        assert_equal(r.height, height)
        assert_equal(r.chamfer, chamfer)
        assert_array_almost_equal(r.corners, corners)

def test_chamfer_rectangle_bounds():
    """ Test chamfer rectangle bounding box calculation
    """
    r = ChamferRectangle((0,0), 2, 2, 0.2, (True, True, False, False))
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))
    r = ChamferRectangle((0,0), 2, 2, 0.2, (True, True, False, False), rotation=45)
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (-math.sqrt(2), math.sqrt(2)))
    assert_array_almost_equal(ybounds, (-math.sqrt(2), math.sqrt(2)))


def test_round_rectangle_ctor():
    """ Test round rectangle creation
    """
    test_cases = (((0,0), 1, 1, 0.2, (True, True, False, False)),
                  ((0, 0), 1, 2, 0.3, (True, True, True, True)),
                  ((1,1), 1, 2, 0.4, (False, False, False, False)))
    for pos, width, height, radius, corners in test_cases:
        r = RoundRectangle(pos, width, height, radius, corners)
        assert_equal(r.position, pos)
        assert_equal(r.width, width)
        assert_equal(r.height, height)
        assert_equal(r.radius, radius)
        assert_array_almost_equal(r.corners, corners)
        
def test_round_rectangle_bounds():
    """ Test round rectangle bounding box calculation
    """
    r = RoundRectangle((0,0), 2, 2, 0.2, (True, True, False, False))
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))
    r = RoundRectangle((0,0), 2, 2, 0.2, (True, True, False, False), rotation=45)
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (-math.sqrt(2), math.sqrt(2)))
    assert_array_almost_equal(ybounds, (-math.sqrt(2), math.sqrt(2)))
    
    
    
    