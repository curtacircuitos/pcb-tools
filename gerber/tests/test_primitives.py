#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..primitives import *
from tests import *


def test_primitive_implementation_warning():
    p = Primitive()
    assert_raises(NotImplementedError, p.bounding_box)


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
    cases = [((0, 0), (1, 1), ((-1, 2), (-1, 2))),
             ((-1, -1), (1, 1), ((-2, 2), (-2, 2))),
             ((1, 1), (-1, -1), ((-2, 2), (-2, 2))),
             ((-1, 1), (1, -1), ((-2, 2), (-2, 2))),]

    c = Circle((0, 0), 2)
    r = Rectangle((0, 0), 2, 2)
    for shape in (c, r):
        for start, end, expected in cases:
            l = Line(start, end, shape)
            assert_equal(l.bounding_box, expected)
    # Test a non-square rectangle
    r = Rectangle((0, 0), 3, 2)
    cases = [((0, 0), (1, 1), ((-1.5, 2.5), (-1, 2))),
             ((-1, -1), (1, 1), ((-2.5, 2.5), (-2, 2))),
             ((1, 1), (-1, -1), ((-2.5, 2.5), (-2, 2))),
             ((-1, 1), (1, -1), ((-2.5, 2.5), (-2, 2))),]
    for start, end, expected in cases:
        l = Line(start, end, r)
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
        c = Circle((0,0), 1)
        a = Arc(start, end, center, direction, c)
        assert_equal(a.sweep_angle, sweep)

def test_arc_bounds():
    """ Test Arc primitive bounding box calculation
    """
    cases = [((1, 0), (0, 1), (0, 0), 'clockwise',  ((-1.5, 1.5), (-1.5, 1.5))),
             ((1, 0), (0, 1), (0, 0), 'counterclockwise',  ((-0.5, 1.5), (-0.5, 1.5))),
             #TODO: ADD MORE TEST CASES HERE
             ]
    for start, end, center, direction, bounds in cases:
        c = Circle((0,0), 1)
        a = Arc(start, end, center, direction, c)
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


def test_obround_ctor():
    """ Test obround creation
    """
    test_cases = (((0,0), 1, 1),
                  ((0, 0), 1, 2),
                  ((1,1), 1, 2))
    for pos, width, height in test_cases:
        o = Obround(pos, width, height)
        assert_equal(o.position, pos)
        assert_equal(o.width, width)
        assert_equal(o.height, height)


def test_obround_bounds():
    """ Test obround bounding box calculation
    """
    o = Obround((2,2),2,4)
    xbounds, ybounds = o.bounding_box
    assert_array_almost_equal(xbounds, (1, 3))
    assert_array_almost_equal(ybounds, (0, 4))
    o = Obround((2,2),4,2)
    xbounds, ybounds = o.bounding_box
    assert_array_almost_equal(xbounds, (0, 4))
    assert_array_almost_equal(ybounds, (1, 3))


def test_obround_orientation():
    o = Obround((0, 0), 2, 1)
    assert_equal(o.orientation, 'horizontal')
    o = Obround((0, 0), 1, 2)
    assert_equal(o.orientation, 'vertical')


def test_obround_subshapes():
    o = Obround((0,0), 1, 4)
    ss = o.subshapes
    assert_array_almost_equal(ss['rectangle'].position, (0, 0))
    assert_array_almost_equal(ss['circle1'].position, (0, 1.5))
    assert_array_almost_equal(ss['circle2'].position, (0, -1.5))
    o = Obround((0,0), 4, 1)
    ss = o.subshapes
    assert_array_almost_equal(ss['rectangle'].position, (0, 0))
    assert_array_almost_equal(ss['circle1'].position, (1.5, 0))
    assert_array_almost_equal(ss['circle2'].position, (-1.5, 0))
    
def test_polygon_ctor():
    """ Test polygon creation
    """
    test_cases = (((0,0), 3, 5),
                  ((0, 0), 5, 6),
                  ((1,1), 7, 7))
    for pos, sides, radius in test_cases:
        p = Polygon(pos, sides, radius)
        assert_equal(p.position, pos)
        assert_equal(p.sides, sides)
        assert_equal(p.radius, radius)
        
def test_polygon_bounds():
    """ Test polygon bounding box calculation
    """
    p = Polygon((2,2), 3, 2)
    xbounds, ybounds = p.bounding_box
    assert_array_almost_equal(xbounds, (0, 4))
    assert_array_almost_equal(ybounds, (0, 4))
    p = Polygon((2,2),3, 4)
    xbounds, ybounds = p.bounding_box
    assert_array_almost_equal(xbounds, (-2, 6))
    assert_array_almost_equal(ybounds, (-2, 6))


def test_region_ctor():
    """ Test Region creation
    """
    points = ((0, 0), (1,0), (1,1), (0,1))
    r = Region(points)
    for i, point in enumerate(points):
        assert_array_almost_equal(r.points[i], point)


def test_region_bounds():
    """ Test region bounding box calculation
    """
    points = ((0, 0), (1,0), (1,1), (0,1))
    r = Region(points)
    xbounds, ybounds = r.bounding_box
    assert_array_almost_equal(xbounds, (0, 1))
    assert_array_almost_equal(ybounds, (0, 1))
    
    
def test_round_butterfly_ctor():
    """ Test round butterfly creation
    """
    test_cases = (((0,0), 3), ((0, 0), 5), ((1,1), 7))
    for pos, diameter in test_cases:
        b = RoundButterfly(pos, diameter)
        assert_equal(b.position, pos)
        assert_equal(b.diameter, diameter)
        assert_equal(b.radius, diameter/2.)

def test_round_butterfly_ctor_validation():
    """ Test RoundButterfly argument validation
    """
    assert_raises(TypeError, RoundButterfly, 3, 5)
    assert_raises(TypeError, RoundButterfly, (3,4,5), 5)

def test_round_butterfly_bounds():
    """ Test RoundButterfly bounding box calculation
    """
    b = RoundButterfly((0, 0), 2)
    xbounds, ybounds = b.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))
    
def test_square_butterfly_ctor():
    """ Test SquareButterfly creation
    """
    test_cases = (((0,0), 3), ((0, 0), 5), ((1,1), 7))
    for pos, side in test_cases:
        b = SquareButterfly(pos, side)
        assert_equal(b.position, pos)
        assert_equal(b.side, side)

def test_square_butterfly_ctor_validation():
    """ Test SquareButterfly argument validation
    """
    assert_raises(TypeError, SquareButterfly, 3, 5)
    assert_raises(TypeError, SquareButterfly, (3,4,5), 5)


def test_square_butterfly_bounds():
    """ Test SquareButterfly bounding box calculation
    """
    b = SquareButterfly((0, 0), 2)
    xbounds, ybounds = b.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))

def test_donut_ctor():
    """ Test Donut primitive creation
    """
    test_cases = (((0,0), 'round', 3, 5), ((0, 0), 'square', 5, 7),
                  ((1,1), 'hexagon', 7, 9), ((2, 2), 'octagon', 9, 11))
    for pos, shape, in_d, out_d in test_cases:
        d = Donut(pos, shape, in_d, out_d)
        assert_equal(d.position, pos)
        assert_equal(d.shape, shape)
        assert_equal(d.inner_diameter, in_d)
        assert_equal(d.outer_diameter, out_d)

def test_donut_ctor_validation():
    assert_raises(TypeError, Donut, 3, 'round', 5, 7)
    assert_raises(TypeError, Donut, (3, 4, 5), 'round', 5, 7)
    assert_raises(ValueError, Donut, (0, 0), 'triangle', 3, 5)
    assert_raises(ValueError, Donut, (0, 0), 'round', 5, 3)
    
def test_donut_bounds():
    pass

def test_drill_ctor():
    """ Test drill primitive creation
    """
    test_cases = (((0, 0), 2), ((1, 1), 3), ((2, 2), 5))
    for position, diameter in test_cases:
        d = Drill(position, diameter)
        assert_equal(d.position, position)
        assert_equal(d.diameter, diameter)
        assert_equal(d.radius, diameter/2.)
    
def test_drill_ctor_validation():
    """ Test drill argument validation
    """
    assert_raises(TypeError, Drill, 3, 5)
    assert_raises(TypeError, Drill, (3,4,5), 5)
    
def test_drill_bounds():
    d = Drill((0, 0), 2)
    xbounds, ybounds = d.bounding_box
    assert_array_almost_equal(xbounds, (-1, 1))
    assert_array_almost_equal(ybounds, (-1, 1))
    d = Drill((1, 2), 2)
    xbounds, ybounds = d.bounding_box
    assert_array_almost_equal(xbounds, (0, 2))
    assert_array_almost_equal(ybounds, (1, 3))
    
    