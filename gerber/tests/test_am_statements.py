#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import *
from ..am_statements import *
from ..am_statements import inch, metric


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


def test_AMPrimitive_conversion():
    p = AMPrimitive(4, 'on')
    assert_raises(NotImplementedError, p.to_inch)
    assert_raises(NotImplementedError, p.to_metric)


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


def test_AMCommentPrimitive_conversion():
    c = AMCommentPrimitive(0, 'Rectangle with rounded corners.')
    ci = c
    cm = c
    ci.to_inch()
    cm.to_metric()
    assert_equal(c, ci)
    assert_equal(c, cm)


def test_AMCommentPrimitive_string():
    c = AMCommentPrimitive(0, 'Test Comment')
    assert_equal(str(c), '<Aperture Macro Comment: Test Comment>')


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
    assert_equal(c.position, (0, 0))


def test_AMCirclePrimitive_dump():
    c = AMCirclePrimitive(1, 'off', 5, (0, 0))
    assert_equal(c.to_gerber(), '1,0,5,0,0*')
    c = AMCirclePrimitive(1, 'on', 5, (0, 0))
    assert_equal(c.to_gerber(), '1,1,5,0,0*')


def test_AMCirclePrimitive_conversion():
    c = AMCirclePrimitive(1, 'off', 25.4, (25.4, 0))
    c.to_inch()
    assert_equal(c.diameter, 1)
    assert_equal(c.position, (1, 0))

    c = AMCirclePrimitive(1, 'off', 1, (1, 0))
    c.to_metric()
    assert_equal(c.diameter, 25.4)
    assert_equal(c.position, (25.4, 0))


def test_AMVectorLinePrimitive_validation():
    assert_raises(ValueError, AMVectorLinePrimitive,
                  3, 'on', 0.1, (0, 0), (3.3, 5.4), 0)


def test_AMVectorLinePrimitive_factory():
    l = AMVectorLinePrimitive.from_gerber('20,1,0.9,0,0.45,12,0.45,0*')
    assert_equal(l.code, 20)
    assert_equal(l.exposure, 'on')
    assert_equal(l.width, 0.9)
    assert_equal(l.start, (0, 0.45))
    assert_equal(l.end, (12, 0.45))
    assert_equal(l.rotation, 0)


def test_AMVectorLinePrimitive_dump():
    l = AMVectorLinePrimitive.from_gerber('20,1,0.9,0,0.45,12,0.45,0*')
    assert_equal(l.to_gerber(), '20,1,0.9,0.0,0.45,12.0,0.45,0.0*')


def test_AMVectorLinePrimtive_conversion():
    l = AMVectorLinePrimitive(20, 'on', 25.4, (0, 0), (25.4, 25.4), 0)
    l.to_inch()
    assert_equal(l.width, 1)
    assert_equal(l.start, (0, 0))
    assert_equal(l.end, (1, 1))

    l = AMVectorLinePrimitive(20, 'on', 1, (0, 0), (1, 1), 0)
    l.to_metric()
    assert_equal(l.width, 25.4)
    assert_equal(l.start, (0, 0))
    assert_equal(l.end, (25.4, 25.4))


def test_AMOutlinePrimitive_validation():
    assert_raises(ValueError, AMOutlinePrimitive, 7, 'on',
                  (0, 0), [(3.3, 5.4), (4.0, 5.4), (0, 0)], 0)
    assert_raises(ValueError, AMOutlinePrimitive, 4, 'on',
                  (0, 0), [(3.3, 5.4), (4.0, 5.4), (0, 1)], 0)


def test_AMOutlinePrimitive_factory():
    o = AMOutlinePrimitive.from_gerber('4,1,3,0,0,3,3,3,0,0,0,0*')
    assert_equal(o.code, 4)
    assert_equal(o.exposure, 'on')
    assert_equal(o.start_point, (0, 0))
    assert_equal(o.points, [(3, 3), (3, 0), (0, 0)])
    assert_equal(o.rotation, 0)


def test_AMOUtlinePrimitive_dump():
    o = AMOutlinePrimitive(4, 'on', (0, 0), [(3, 3), (3, 0), (0, 0)], 0)
    # New lines don't matter for Gerber, but we insert them to make it easier to remove
    # For test purposes we can ignore them
    assert_equal(o.to_gerber().replace('\n', ''), '4,1,3,0,0,3,3,3,0,0,0,0*')




def test_AMOutlinePrimitive_conversion():
    o = AMOutlinePrimitive(
        4, 'on', (0, 0), [(25.4, 25.4), (25.4, 0), (0, 0)], 0)
    o.to_inch()
    assert_equal(o.start_point, (0, 0))
    assert_equal(o.points, ((1., 1.), (1., 0.), (0., 0.)))

    o = AMOutlinePrimitive(4, 'on', (0, 0), [(1, 1), (1, 0), (0, 0)], 0)
    o.to_metric()
    assert_equal(o.start_point, (0, 0))
    assert_equal(o.points, ((25.4, 25.4), (25.4, 0), (0, 0)))


def test_AMPolygonPrimitive_validation():
    assert_raises(ValueError, AMPolygonPrimitive, 6, 'on', 3, (3.3, 5.4), 3, 0)
    assert_raises(ValueError, AMPolygonPrimitive, 5, 'on', 2, (3.3, 5.4), 3, 0)
    assert_raises(ValueError, AMPolygonPrimitive, 5, 'on', 13, (3.3, 5.4), 3, 0)


def test_AMPolygonPrimitive_factory():
    p = AMPolygonPrimitive.from_gerber('5,1,3,3.3,5.4,3,0')
    assert_equal(p.code, 5)
    assert_equal(p.exposure, 'on')
    assert_equal(p.vertices, 3)
    assert_equal(p.position, (3.3, 5.4))
    assert_equal(p.diameter, 3)
    assert_equal(p.rotation, 0)


def test_AMPolygonPrimitive_dump():
    p = AMPolygonPrimitive(5, 'on', 3, (3.3, 5.4), 3, 0)
    assert_equal(p.to_gerber(), '5,1,3,3.3,5.4,3,0*')


def test_AMPolygonPrimitive_conversion():
    p = AMPolygonPrimitive(5, 'off', 3, (25.4, 0), 25.4, 0)
    p.to_inch()
    assert_equal(p.diameter, 1)
    assert_equal(p.position, (1, 0))

    p = AMPolygonPrimitive(5, 'off', 3, (1, 0), 1, 0)
    p.to_metric()
    assert_equal(p.diameter, 25.4)
    assert_equal(p.position, (25.4, 0))


def test_AMMoirePrimitive_validation():
    assert_raises(ValueError, AMMoirePrimitive, 7,
                  (0, 0), 5.1, 0.2, 0.4, 6, 0.1, 6.1, 0)


def test_AMMoirePrimitive_factory():
    m = AMMoirePrimitive.from_gerber('6,0,0,5,0.5,0.5,2,0.1,6,0*')
    assert_equal(m.code, 6)
    assert_equal(m.position, (0, 0))
    assert_equal(m.diameter, 5)
    assert_equal(m.ring_thickness, 0.5)
    assert_equal(m.gap, 0.5)
    assert_equal(m.max_rings, 2)
    assert_equal(m.crosshair_thickness, 0.1)
    assert_equal(m.crosshair_length, 6)
    assert_equal(m.rotation, 0)


def test_AMMoirePrimitive_dump():
    m = AMMoirePrimitive.from_gerber('6,0,0,5,0.5,0.5,2,0.1,6,0*')
    assert_equal(m.to_gerber(), '6,0,0,5.0,0.5,0.5,2,0.1,6.0,0.0*')


def test_AMMoirePrimitive_conversion():
    m = AMMoirePrimitive(6, (25.4, 25.4), 25.4, 25.4, 25.4, 6, 25.4, 25.4, 0)
    m.to_inch()
    assert_equal(m.position, (1., 1.))
    assert_equal(m.diameter, 1.)
    assert_equal(m.ring_thickness, 1.)
    assert_equal(m.gap, 1.)
    assert_equal(m.crosshair_thickness, 1.)
    assert_equal(m.crosshair_length, 1.)

    m = AMMoirePrimitive(6, (1, 1), 1, 1, 1, 6, 1, 1, 0)
    m.to_metric()
    assert_equal(m.position, (25.4, 25.4))
    assert_equal(m.diameter, 25.4)
    assert_equal(m.ring_thickness, 25.4)
    assert_equal(m.gap, 25.4)
    assert_equal(m.crosshair_thickness, 25.4)
    assert_equal(m.crosshair_length, 25.4)


def test_AMThermalPrimitive_validation():
    assert_raises(ValueError, AMThermalPrimitive, 8, (0.0, 0.0), 7, 5, 0.2, 0.0)
    assert_raises(TypeError, AMThermalPrimitive, 7, (0.0, '0'), 7, 5, 0.2, 0.0)




def test_AMThermalPrimitive_factory():
    t = AMThermalPrimitive.from_gerber('7,0,0,7,6,0.2,45*')
    assert_equal(t.code, 7)
    assert_equal(t.position, (0, 0))
    assert_equal(t.outer_diameter, 7)
    assert_equal(t.inner_diameter, 6)
    assert_equal(t.gap, 0.2)
    assert_equal(t.rotation, 45)




def test_AMThermalPrimitive_dump():
    t = AMThermalPrimitive.from_gerber('7,0,0,7,6,0.2,30*')
    assert_equal(t.to_gerber(), '7,0,0,7.0,6.0,0.2,30.0*')




def test_AMThermalPrimitive_conversion():
    t = AMThermalPrimitive(7, (25.4, 25.4), 25.4, 25.4, 25.4, 0.0)
    t.to_inch()
    assert_equal(t.position, (1., 1.))
    assert_equal(t.outer_diameter, 1.)
    assert_equal(t.inner_diameter, 1.)
    assert_equal(t.gap, 1.)

    t = AMThermalPrimitive(7, (1, 1), 1, 1, 1, 0)
    t.to_metric()
    assert_equal(t.position, (25.4, 25.4))
    assert_equal(t.outer_diameter, 25.4)
    assert_equal(t.inner_diameter, 25.4)
    assert_equal(t.gap, 25.4)


def test_AMCenterLinePrimitive_validation():
    assert_raises(ValueError, AMCenterLinePrimitive,
                  22, 1, 0.2, 0.5, (0, 0), 0)


def test_AMCenterLinePrimtive_factory():
    l = AMCenterLinePrimitive.from_gerber('21,1,6.8,1.2,3.4,0.6,0*')
    assert_equal(l.code, 21)
    assert_equal(l.exposure, 'on')
    assert_equal(l.width, 6.8)
    assert_equal(l.height, 1.2)
    assert_equal(l.center, (3.4, 0.6))
    assert_equal(l.rotation, 0)


def test_AMCenterLinePrimitive_dump():
    l = AMCenterLinePrimitive.from_gerber('21,1,6.8,1.2,3.4,0.6,0*')
    assert_equal(l.to_gerber(), '21,1,6.8,1.2,3.4,0.6,0.0*')


def test_AMCenterLinePrimitive_conversion():
    l = AMCenterLinePrimitive(21, 'on', 25.4, 25.4, (25.4, 25.4), 0)
    l.to_inch()
    assert_equal(l.width, 1.)
    assert_equal(l.height, 1.)
    assert_equal(l.center, (1., 1.))

    l = AMCenterLinePrimitive(21, 'on', 1, 1, (1, 1), 0)
    l.to_metric()
    assert_equal(l.width, 25.4)
    assert_equal(l.height, 25.4)
    assert_equal(l.center, (25.4, 25.4))


def test_AMLowerLeftLinePrimitive_validation():
    assert_raises(ValueError, AMLowerLeftLinePrimitive,
                  23, 1, 0.2, 0.5, (0, 0), 0)


def test_AMLowerLeftLinePrimtive_factory():
    l = AMLowerLeftLinePrimitive.from_gerber('22,1,6.8,1.2,3.4,0.6,0*')
    assert_equal(l.code, 22)
    assert_equal(l.exposure, 'on')
    assert_equal(l.width, 6.8)
    assert_equal(l.height, 1.2)
    assert_equal(l.lower_left, (3.4, 0.6))
    assert_equal(l.rotation, 0)


def test_AMLowerLeftLinePrimitive_dump():
    l = AMLowerLeftLinePrimitive.from_gerber('22,1,6.8,1.2,3.4,0.6,0*')
    assert_equal(l.to_gerber(), '22,1,6.8,1.2,3.4,0.6,0.0*')


def test_AMLowerLeftLinePrimitive_conversion():
    l = AMLowerLeftLinePrimitive(22, 'on', 25.4, 25.4, (25.4, 25.4), 0)
    l.to_inch()
    assert_equal(l.width, 1.)
    assert_equal(l.height, 1.)
    assert_equal(l.lower_left, (1., 1.))

    l = AMLowerLeftLinePrimitive(22, 'on', 1, 1, (1, 1), 0)
    l.to_metric()
    assert_equal(l.width, 25.4)
    assert_equal(l.height, 25.4)
    assert_equal(l.lower_left, (25.4, 25.4))


def test_AMUnsupportPrimitive():
    u = AMUnsupportPrimitive.from_gerber('Test')
    assert_equal(u.primitive, 'Test')
    u = AMUnsupportPrimitive('Test')
    assert_equal(u.to_gerber(), 'Test')


def test_AMUnsupportPrimitive_smoketest():
    u = AMUnsupportPrimitive.from_gerber('Test')
    u.to_inch()
    u.to_metric()


def test_inch():
    assert_equal(inch(25.4), 1)


def test_metric():
    assert_equal(metric(1), 25.4)
