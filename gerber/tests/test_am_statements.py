#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

import pytest

from ..am_statements import *
from ..am_statements import inch, metric


def test_AMPrimitive_ctor():
    for exposure in ("on", "off", "ON", "OFF"):
        for code in (0, 1, 2, 4, 5, 6, 7, 20, 21, 22):
            p = AMPrimitive(code, exposure)
            assert p.code == code
            assert p.exposure == exposure.lower()


def test_AMPrimitive_validation():
    pytest.raises(TypeError, AMPrimitive, "1", "off")
    pytest.raises(ValueError, AMPrimitive, 0, "exposed")
    pytest.raises(ValueError, AMPrimitive, 3, "off")


def test_AMPrimitive_conversion():
    p = AMPrimitive(4, "on")
    pytest.raises(NotImplementedError, p.to_inch)
    pytest.raises(NotImplementedError, p.to_metric)


def test_AMCommentPrimitive_ctor():
    c = AMCommentPrimitive(0, " This is a comment *")
    assert c.code == 0
    assert c.comment == "This is a comment"


def test_AMCommentPrimitive_validation():
    pytest.raises(ValueError, AMCommentPrimitive, 1, "This is a comment")


def test_AMCommentPrimitive_factory():
    c = AMCommentPrimitive.from_gerber("0 Rectangle with rounded corners. *")
    assert c.code == 0
    assert c.comment == "Rectangle with rounded corners."


def test_AMCommentPrimitive_dump():
    c = AMCommentPrimitive(0, "Rectangle with rounded corners.")
    assert c.to_gerber() == "0 Rectangle with rounded corners. *"


def test_AMCommentPrimitive_conversion():
    c = AMCommentPrimitive(0, "Rectangle with rounded corners.")
    ci = c
    cm = c
    ci.to_inch()
    cm.to_metric()
    assert c == ci
    assert c == cm


def test_AMCommentPrimitive_string():
    c = AMCommentPrimitive(0, "Test Comment")
    assert str(c) == "<Aperture Macro Comment: Test Comment>"


def test_AMCirclePrimitive_ctor():
    test_cases = (
        (1, "on", 0, (0, 0)),
        (1, "off", 1, (0, 1)),
        (1, "on", 2.5, (0, 2)),
        (1, "off", 5.0, (3, 3)),
    )
    for code, exposure, diameter, position in test_cases:
        c = AMCirclePrimitive(code, exposure, diameter, position)
        assert c.code == code
        assert c.exposure == exposure
        assert c.diameter == diameter
        assert c.position == position


def test_AMCirclePrimitive_validation():
    pytest.raises(ValueError, AMCirclePrimitive, 2, "on", 0, (0, 0))


def test_AMCirclePrimitive_factory():
    c = AMCirclePrimitive.from_gerber("1,0,5,0,0*")
    assert c.code == 1
    assert c.exposure == "off"
    assert c.diameter == 5
    assert c.position == (0, 0)


def test_AMCirclePrimitive_dump():
    c = AMCirclePrimitive(1, "off", 5, (0, 0))
    assert c.to_gerber() == "1,0,5,0,0*"
    c = AMCirclePrimitive(1, "on", 5, (0, 0))
    assert c.to_gerber() == "1,1,5,0,0*"


def test_AMCirclePrimitive_conversion():
    c = AMCirclePrimitive(1, "off", 25.4, (25.4, 0))
    c.to_inch()
    assert c.diameter == 1
    assert c.position == (1, 0)

    c = AMCirclePrimitive(1, "off", 1, (1, 0))
    c.to_metric()
    assert c.diameter == 25.4
    assert c.position == (25.4, 0)


def test_AMVectorLinePrimitive_validation():
    pytest.raises(
        ValueError, AMVectorLinePrimitive, 3, "on", 0.1, (0, 0), (3.3, 5.4), 0
    )


def test_AMVectorLinePrimitive_factory():
    l = AMVectorLinePrimitive.from_gerber("20,1,0.9,0,0.45,12,0.45,0*")
    assert l.code == 20
    assert l.exposure == "on"
    assert l.width == 0.9
    assert l.start == (0, 0.45)
    assert l.end == (12, 0.45)
    assert l.rotation == 0


def test_AMVectorLinePrimitive_dump():
    l = AMVectorLinePrimitive.from_gerber("20,1,0.9,0,0.45,12,0.45,0*")
    assert l.to_gerber() == "20,1,0.9,0.0,0.45,12.0,0.45,0.0*"


def test_AMVectorLinePrimtive_conversion():
    l = AMVectorLinePrimitive(20, "on", 25.4, (0, 0), (25.4, 25.4), 0)
    l.to_inch()
    assert l.width == 1
    assert l.start == (0, 0)
    assert l.end == (1, 1)

    l = AMVectorLinePrimitive(20, "on", 1, (0, 0), (1, 1), 0)
    l.to_metric()
    assert l.width == 25.4
    assert l.start == (0, 0)
    assert l.end == (25.4, 25.4)


def test_AMOutlinePrimitive_validation():
    pytest.raises(
        ValueError,
        AMOutlinePrimitive,
        7,
        "on",
        (0, 0),
        [(3.3, 5.4), (4.0, 5.4), (0, 0)],
        0,
    )
    pytest.raises(
        ValueError,
        AMOutlinePrimitive,
        4,
        "on",
        (0, 0),
        [(3.3, 5.4), (4.0, 5.4), (0, 1)],
        0,
    )


def test_AMOutlinePrimitive_factory():
    o = AMOutlinePrimitive.from_gerber("4,1,3,0,0,3,3,3,0,0,0,0*")
    assert o.code == 4
    assert o.exposure == "on"
    assert o.start_point == (0, 0)
    assert o.points == [(3, 3), (3, 0), (0, 0)]
    assert o.rotation == 0


def test_AMOUtlinePrimitive_dump():
    o = AMOutlinePrimitive(4, "on", (0, 0), [(3, 3), (3, 0), (0, 0)], 0)
    # New lines don't matter for Gerber, but we insert them to make it easier to remove
    # For test purposes we can ignore them
    assert o.to_gerber().replace("\n", "") == "4,1,3,0,0,3,3,3,0,0,0,0*"


def test_AMOutlinePrimitive_conversion():
    o = AMOutlinePrimitive(4, "on", (0, 0), [(25.4, 25.4), (25.4, 0), (0, 0)], 0)
    o.to_inch()
    assert o.start_point == (0, 0)
    assert o.points == ((1.0, 1.0), (1.0, 0.0), (0.0, 0.0))

    o = AMOutlinePrimitive(4, "on", (0, 0), [(1, 1), (1, 0), (0, 0)], 0)
    o.to_metric()
    assert o.start_point == (0, 0)
    assert o.points == ((25.4, 25.4), (25.4, 0), (0, 0))


def test_AMPolygonPrimitive_validation():
    pytest.raises(ValueError, AMPolygonPrimitive, 6, "on", 3, (3.3, 5.4), 3, 0)
    pytest.raises(ValueError, AMPolygonPrimitive, 5, "on", 2, (3.3, 5.4), 3, 0)
    pytest.raises(ValueError, AMPolygonPrimitive, 5, "on", 13, (3.3, 5.4), 3, 0)


def test_AMPolygonPrimitive_factory():
    p = AMPolygonPrimitive.from_gerber("5,1,3,3.3,5.4,3,0")
    assert p.code == 5
    assert p.exposure == "on"
    assert p.vertices == 3
    assert p.position == (3.3, 5.4)
    assert p.diameter == 3
    assert p.rotation == 0


def test_AMPolygonPrimitive_dump():
    p = AMPolygonPrimitive(5, "on", 3, (3.3, 5.4), 3, 0)
    assert p.to_gerber() == "5,1,3,3.3,5.4,3,0*"


def test_AMPolygonPrimitive_conversion():
    p = AMPolygonPrimitive(5, "off", 3, (25.4, 0), 25.4, 0)
    p.to_inch()
    assert p.diameter == 1
    assert p.position == (1, 0)

    p = AMPolygonPrimitive(5, "off", 3, (1, 0), 1, 0)
    p.to_metric()
    assert p.diameter == 25.4
    assert p.position == (25.4, 0)


def test_AMMoirePrimitive_validation():
    pytest.raises(
        ValueError, AMMoirePrimitive, 7, (0, 0), 5.1, 0.2, 0.4, 6, 0.1, 6.1, 0
    )


def test_AMMoirePrimitive_factory():
    m = AMMoirePrimitive.from_gerber("6,0,0,5,0.5,0.5,2,0.1,6,0*")
    assert m.code == 6
    assert m.position == (0, 0)
    assert m.diameter == 5
    assert m.ring_thickness == 0.5
    assert m.gap == 0.5
    assert m.max_rings == 2
    assert m.crosshair_thickness == 0.1
    assert m.crosshair_length == 6
    assert m.rotation == 0


def test_AMMoirePrimitive_dump():
    m = AMMoirePrimitive.from_gerber("6,0,0,5,0.5,0.5,2,0.1,6,0*")
    assert m.to_gerber() == "6,0,0,5.0,0.5,0.5,2,0.1,6.0,0.0*"


def test_AMMoirePrimitive_conversion():
    m = AMMoirePrimitive(6, (25.4, 25.4), 25.4, 25.4, 25.4, 6, 25.4, 25.4, 0)
    m.to_inch()
    assert m.position == (1.0, 1.0)
    assert m.diameter == 1.0
    assert m.ring_thickness == 1.0
    assert m.gap == 1.0
    assert m.crosshair_thickness == 1.0
    assert m.crosshair_length == 1.0

    m = AMMoirePrimitive(6, (1, 1), 1, 1, 1, 6, 1, 1, 0)
    m.to_metric()
    assert m.position == (25.4, 25.4)
    assert m.diameter == 25.4
    assert m.ring_thickness == 25.4
    assert m.gap == 25.4
    assert m.crosshair_thickness == 25.4
    assert m.crosshair_length == 25.4


def test_AMThermalPrimitive_validation():
    pytest.raises(ValueError, AMThermalPrimitive, 8, (0.0, 0.0), 7, 5, 0.2, 0.0)
    pytest.raises(TypeError, AMThermalPrimitive, 7, (0.0, "0"), 7, 5, 0.2, 0.0)


def test_AMThermalPrimitive_factory():
    t = AMThermalPrimitive.from_gerber("7,0,0,7,6,0.2,45*")
    assert t.code == 7
    assert t.position == (0, 0)
    assert t.outer_diameter == 7
    assert t.inner_diameter == 6
    assert t.gap == 0.2
    assert t.rotation == 45


def test_AMThermalPrimitive_dump():
    t = AMThermalPrimitive.from_gerber("7,0,0,7,6,0.2,30*")
    assert t.to_gerber() == "7,0,0,7.0,6.0,0.2,30.0*"


def test_AMThermalPrimitive_conversion():
    t = AMThermalPrimitive(7, (25.4, 25.4), 25.4, 25.4, 25.4, 0.0)
    t.to_inch()
    assert t.position == (1.0, 1.0)
    assert t.outer_diameter == 1.0
    assert t.inner_diameter == 1.0
    assert t.gap == 1.0

    t = AMThermalPrimitive(7, (1, 1), 1, 1, 1, 0)
    t.to_metric()
    assert t.position == (25.4, 25.4)
    assert t.outer_diameter == 25.4
    assert t.inner_diameter == 25.4
    assert t.gap == 25.4


def test_AMCenterLinePrimitive_validation():
    pytest.raises(ValueError, AMCenterLinePrimitive, 22, 1, 0.2, 0.5, (0, 0), 0)


def test_AMCenterLinePrimtive_factory():
    l = AMCenterLinePrimitive.from_gerber("21,1,6.8,1.2,3.4,0.6,0*")
    assert l.code == 21
    assert l.exposure == "on"
    assert l.width == 6.8
    assert l.height == 1.2
    assert l.center == (3.4, 0.6)
    assert l.rotation == 0


def test_AMCenterLinePrimitive_dump():
    l = AMCenterLinePrimitive.from_gerber("21,1,6.8,1.2,3.4,0.6,0*")
    assert l.to_gerber() == "21,1,6.8,1.2,3.4,0.6,0.0*"


def test_AMCenterLinePrimitive_conversion():
    l = AMCenterLinePrimitive(21, "on", 25.4, 25.4, (25.4, 25.4), 0)
    l.to_inch()
    assert l.width == 1.0
    assert l.height == 1.0
    assert l.center == (1.0, 1.0)

    l = AMCenterLinePrimitive(21, "on", 1, 1, (1, 1), 0)
    l.to_metric()
    assert l.width == 25.4
    assert l.height == 25.4
    assert l.center == (25.4, 25.4)


def test_AMLowerLeftLinePrimitive_validation():
    pytest.raises(ValueError, AMLowerLeftLinePrimitive, 23, 1, 0.2, 0.5, (0, 0), 0)


def test_AMLowerLeftLinePrimtive_factory():
    l = AMLowerLeftLinePrimitive.from_gerber("22,1,6.8,1.2,3.4,0.6,0*")
    assert l.code == 22
    assert l.exposure == "on"
    assert l.width == 6.8
    assert l.height == 1.2
    assert l.lower_left == (3.4, 0.6)
    assert l.rotation == 0


def test_AMLowerLeftLinePrimitive_dump():
    l = AMLowerLeftLinePrimitive.from_gerber("22,1,6.8,1.2,3.4,0.6,0*")
    assert l.to_gerber() == "22,1,6.8,1.2,3.4,0.6,0.0*"


def test_AMLowerLeftLinePrimitive_conversion():
    l = AMLowerLeftLinePrimitive(22, "on", 25.4, 25.4, (25.4, 25.4), 0)
    l.to_inch()
    assert l.width == 1.0
    assert l.height == 1.0
    assert l.lower_left == (1.0, 1.0)

    l = AMLowerLeftLinePrimitive(22, "on", 1, 1, (1, 1), 0)
    l.to_metric()
    assert l.width == 25.4
    assert l.height == 25.4
    assert l.lower_left == (25.4, 25.4)


def test_AMUnsupportPrimitive():
    u = AMUnsupportPrimitive.from_gerber("Test")
    assert u.primitive == "Test"
    u = AMUnsupportPrimitive("Test")
    assert u.to_gerber() == "Test"


def test_AMUnsupportPrimitive_smoketest():
    u = AMUnsupportPrimitive.from_gerber("Test")
    u.to_inch()
    u.to_metric()


def test_inch():
    assert inch(25.4) == 1


def test_metric():
    assert metric(1) == 25.4
