#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

import pytest
from ..gerber_statements import *
from ..cam import FileSettings


def test_Statement_smoketest():
    stmt = Statement("Test")
    assert stmt.type == "Test"
    stmt.to_metric()
    assert "units=metric" in str(stmt)
    stmt.to_inch()
    assert "units=inch" in str(stmt)
    stmt.to_metric()
    stmt.offset(1, 1)
    assert "type=Test" in str(stmt)


def test_FSParamStmt_factory():
    """ Test FSParamStruct factory
    """
    stmt = {"param": "FS", "zero": "L", "notation": "A", "x": "27"}
    fs = FSParamStmt.from_dict(stmt)
    assert fs.param == "FS"
    assert fs.zero_suppression == "leading"
    assert fs.notation == "absolute"
    assert fs.format == (2, 7)

    stmt = {"param": "FS", "zero": "T", "notation": "I", "x": "27"}
    fs = FSParamStmt.from_dict(stmt)
    assert fs.param == "FS"
    assert fs.zero_suppression == "trailing"
    assert fs.notation == "incremental"
    assert fs.format == (2, 7)


def test_FSParamStmt():
    """ Test FSParamStmt initialization
    """
    param = "FS"
    zeros = "trailing"
    notation = "absolute"
    fmt = (2, 5)
    stmt = FSParamStmt(param, zeros, notation, fmt)
    assert stmt.param == param
    assert stmt.zero_suppression == zeros
    assert stmt.notation == notation
    assert stmt.format == fmt


def test_FSParamStmt_dump():
    """ Test FSParamStmt to_gerber()
    """
    stmt = {"param": "FS", "zero": "L", "notation": "A", "x": "27"}
    fs = FSParamStmt.from_dict(stmt)
    assert fs.to_gerber() == "%FSLAX27Y27*%"

    stmt = {"param": "FS", "zero": "T", "notation": "I", "x": "25"}
    fs = FSParamStmt.from_dict(stmt)
    assert fs.to_gerber() == "%FSTIX25Y25*%"

    settings = FileSettings(zero_suppression="leading", notation="absolute")
    assert fs.to_gerber(settings) == "%FSLAX25Y25*%"


def test_FSParamStmt_string():
    """ Test FSParamStmt.__str__()
    """
    stmt = {"param": "FS", "zero": "L", "notation": "A", "x": "27"}
    fs = FSParamStmt.from_dict(stmt)
    assert str(fs) == "<Format Spec: 2:7 leading zero suppression absolute notation>"

    stmt = {"param": "FS", "zero": "T", "notation": "I", "x": "25"}
    fs = FSParamStmt.from_dict(stmt)
    assert (
        str(fs) == "<Format Spec: 2:5 trailing zero suppression incremental notation>"
    )


def test_MOParamStmt_factory():
    """ Test MOParamStruct factory
    """
    stmts = [{"param": "MO", "mo": "IN"}, {"param": "MO", "mo": "in"}]
    for stmt in stmts:
        mo = MOParamStmt.from_dict(stmt)
        assert mo.param == "MO"
        assert mo.mode == "inch"

    stmts = [{"param": "MO", "mo": "MM"}, {"param": "MO", "mo": "mm"}]
    for stmt in stmts:
        mo = MOParamStmt.from_dict(stmt)
        assert mo.param == "MO"
        assert mo.mode == "metric"

    stmt = {"param": "MO"}
    mo = MOParamStmt.from_dict(stmt)
    assert mo.mode == None
    stmt = {"param": "MO", "mo": "degrees kelvin"}
    pytest.raises(ValueError, MOParamStmt.from_dict, stmt)


def test_MOParamStmt():
    """ Test MOParamStmt initialization
    """
    param = "MO"
    mode = "inch"
    stmt = MOParamStmt(param, mode)
    assert stmt.param == param

    for mode in ["inch", "metric"]:
        stmt = MOParamStmt(param, mode)
        assert stmt.mode == mode


def test_MOParamStmt_dump():
    """ Test MOParamStmt to_gerber()
    """
    stmt = {"param": "MO", "mo": "IN"}
    mo = MOParamStmt.from_dict(stmt)
    assert mo.to_gerber() == "%MOIN*%"

    stmt = {"param": "MO", "mo": "MM"}
    mo = MOParamStmt.from_dict(stmt)
    assert mo.to_gerber() == "%MOMM*%"


def test_MOParamStmt_conversion():
    stmt = {"param": "MO", "mo": "MM"}
    mo = MOParamStmt.from_dict(stmt)
    mo.to_inch()
    assert mo.mode == "inch"

    stmt = {"param": "MO", "mo": "IN"}
    mo = MOParamStmt.from_dict(stmt)
    mo.to_metric()
    assert mo.mode == "metric"


def test_MOParamStmt_string():
    """ Test MOParamStmt.__str__()
    """
    stmt = {"param": "MO", "mo": "IN"}
    mo = MOParamStmt.from_dict(stmt)
    assert str(mo) == "<Mode: inches>"

    stmt = {"param": "MO", "mo": "MM"}
    mo = MOParamStmt.from_dict(stmt)
    assert str(mo) == "<Mode: millimeters>"


def test_IPParamStmt_factory():
    """ Test IPParamStruct factory
    """
    stmt = {"param": "IP", "ip": "POS"}
    ip = IPParamStmt.from_dict(stmt)
    assert ip.ip == "positive"

    stmt = {"param": "IP", "ip": "NEG"}
    ip = IPParamStmt.from_dict(stmt)
    assert ip.ip == "negative"


def test_IPParamStmt():
    """ Test IPParamStmt initialization
    """
    param = "IP"
    for ip in ["positive", "negative"]:
        stmt = IPParamStmt(param, ip)
        assert stmt.param == param
        assert stmt.ip == ip


def test_IPParamStmt_dump():
    """ Test IPParamStmt to_gerber()
    """
    stmt = {"param": "IP", "ip": "POS"}
    ip = IPParamStmt.from_dict(stmt)
    assert ip.to_gerber() == "%IPPOS*%"

    stmt = {"param": "IP", "ip": "NEG"}
    ip = IPParamStmt.from_dict(stmt)
    assert ip.to_gerber() == "%IPNEG*%"


def test_IPParamStmt_string():
    stmt = {"param": "IP", "ip": "POS"}
    ip = IPParamStmt.from_dict(stmt)
    assert str(ip) == "<Image Polarity: positive>"

    stmt = {"param": "IP", "ip": "NEG"}
    ip = IPParamStmt.from_dict(stmt)
    assert str(ip) == "<Image Polarity: negative>"


def test_IRParamStmt_factory():
    stmt = {"param": "IR", "angle": "45"}
    ir = IRParamStmt.from_dict(stmt)
    assert ir.param == "IR"
    assert ir.angle == 45


def test_IRParamStmt_dump():
    stmt = {"param": "IR", "angle": "45"}
    ir = IRParamStmt.from_dict(stmt)
    assert ir.to_gerber() == "%IR45*%"


def test_IRParamStmt_string():
    stmt = {"param": "IR", "angle": "45"}
    ir = IRParamStmt.from_dict(stmt)
    assert str(ir) == "<Image Angle: 45>"


def test_OFParamStmt_factory():
    """ Test OFParamStmt factory
    """
    stmt = {"param": "OF", "a": "0.1234567", "b": "0.1234567"}
    of = OFParamStmt.from_dict(stmt)
    assert of.a == 0.1234567
    assert of.b == 0.1234567


def test_OFParamStmt():
    """ Test IPParamStmt initialization
    """
    param = "OF"
    for val in [0.0, -3.4567]:
        stmt = OFParamStmt(param, val, val)
        assert stmt.param == param
        assert stmt.a == val
        assert stmt.b == val


def test_OFParamStmt_dump():
    """ Test OFParamStmt to_gerber()
    """
    stmt = {"param": "OF", "a": "0.123456", "b": "0.123456"}
    of = OFParamStmt.from_dict(stmt)
    assert of.to_gerber() == "%OFA0.12345B0.12345*%"


def test_OFParamStmt_conversion():
    stmt = {"param": "OF", "a": "2.54", "b": "25.4"}
    of = OFParamStmt.from_dict(stmt)
    of.units = "metric"

    # No effect
    of.to_metric()
    assert of.a == 2.54
    assert of.b == 25.4

    of.to_inch()
    assert of.units == "inch"
    assert of.a == 0.1
    assert of.b == 1.0

    # No effect
    of.to_inch()
    assert of.a == 0.1
    assert of.b == 1.0

    stmt = {"param": "OF", "a": "0.1", "b": "1.0"}
    of = OFParamStmt.from_dict(stmt)
    of.units = "inch"

    # No effect
    of.to_inch()
    assert of.a == 0.1
    assert of.b == 1.0

    of.to_metric()
    assert of.units == "metric"
    assert of.a == 2.54
    assert of.b == 25.4

    # No effect
    of.to_metric()
    assert of.a == 2.54
    assert of.b == 25.4


def test_OFParamStmt_offset():
    s = OFParamStmt("OF", 0, 0)
    s.offset(1, 0)
    assert s.a == 1.0
    assert s.b == 0.0
    s.offset(0, 1)
    assert s.a == 1.0
    assert s.b == 1.0


def test_OFParamStmt_string():
    """ Test OFParamStmt __str__
    """
    stmt = {"param": "OF", "a": "0.123456", "b": "0.123456"}
    of = OFParamStmt.from_dict(stmt)
    assert str(of) == "<Offset: X: 0.123456 Y: 0.123456 >"


def test_SFParamStmt_factory():
    stmt = {"param": "SF", "a": "1.4", "b": "0.9"}
    sf = SFParamStmt.from_dict(stmt)
    assert sf.param == "SF"
    assert sf.a == 1.4
    assert sf.b == 0.9


def test_SFParamStmt_dump():
    stmt = {"param": "SF", "a": "1.4", "b": "0.9"}
    sf = SFParamStmt.from_dict(stmt)
    assert sf.to_gerber() == "%SFA1.4B0.9*%"


def test_SFParamStmt_conversion():
    stmt = {"param": "OF", "a": "2.54", "b": "25.4"}
    of = SFParamStmt.from_dict(stmt)
    of.units = "metric"
    of.to_metric()

    # No effect
    assert of.a == 2.54
    assert of.b == 25.4

    of.to_inch()
    assert of.units == "inch"
    assert of.a == 0.1
    assert of.b == 1.0

    # No effect
    of.to_inch()
    assert of.a == 0.1
    assert of.b == 1.0

    stmt = {"param": "OF", "a": "0.1", "b": "1.0"}
    of = SFParamStmt.from_dict(stmt)
    of.units = "inch"

    # No effect
    of.to_inch()
    assert of.a == 0.1
    assert of.b == 1.0

    of.to_metric()
    assert of.units == "metric"
    assert of.a == 2.54
    assert of.b == 25.4

    # No effect
    of.to_metric()
    assert of.a == 2.54
    assert of.b == 25.4


def test_SFParamStmt_offset():
    s = SFParamStmt("OF", 0, 0)
    s.offset(1, 0)
    assert s.a == 1.0
    assert s.b == 0.0
    s.offset(0, 1)
    assert s.a == 1.0
    assert s.b == 1.0


def test_SFParamStmt_string():
    stmt = {"param": "SF", "a": "1.4", "b": "0.9"}
    sf = SFParamStmt.from_dict(stmt)
    assert str(sf) == "<Scale Factor: X: 1.4 Y: 0.9>"


def test_LPParamStmt_factory():
    """ Test LPParamStmt factory
    """
    stmt = {"param": "LP", "lp": "C"}
    lp = LPParamStmt.from_dict(stmt)
    assert lp.lp == "clear"

    stmt = {"param": "LP", "lp": "D"}
    lp = LPParamStmt.from_dict(stmt)
    assert lp.lp == "dark"


def test_LPParamStmt_dump():
    """ Test LPParamStmt to_gerber()
    """
    stmt = {"param": "LP", "lp": "C"}
    lp = LPParamStmt.from_dict(stmt)
    assert lp.to_gerber() == "%LPC*%"

    stmt = {"param": "LP", "lp": "D"}
    lp = LPParamStmt.from_dict(stmt)
    assert lp.to_gerber() == "%LPD*%"


def test_LPParamStmt_string():
    """ Test LPParamStmt.__str__()
    """
    stmt = {"param": "LP", "lp": "D"}
    lp = LPParamStmt.from_dict(stmt)
    assert str(lp) == "<Level Polarity: dark>"

    stmt = {"param": "LP", "lp": "C"}
    lp = LPParamStmt.from_dict(stmt)
    assert str(lp) == "<Level Polarity: clear>"


def test_AMParamStmt_factory():
    name = "DONUTVAR"
    macro = """0 Test Macro. *
1,1,1.5,0,0*
20,1,0.9,0,0.45,12,0.45,0*
21,1,6.8,1.2,3.4,0.6,0*
22,1,6.8,1.2,0,0,0*
4,1,4,0.1,0.1,0.5,0.1,0.5,0.5,0.1,0.5,0.1,0.1,0*
5,1,8,0,0,8,0*
6,0,0,5,0.5,0.5,2,0.1,6,0*
7,0,0,7,6,0.2,0*
8,THIS IS AN UNSUPPORTED PRIMITIVE*
"""
    s = AMParamStmt.from_dict({"param": "AM", "name": name, "macro": macro})
    s.build()
    assert len(s.primitives) == 10
    assert isinstance(s.primitives[0], AMCommentPrimitive)
    assert isinstance(s.primitives[1], AMCirclePrimitive)
    assert isinstance(s.primitives[2], AMVectorLinePrimitive)
    assert isinstance(s.primitives[3], AMCenterLinePrimitive)
    assert isinstance(s.primitives[4], AMLowerLeftLinePrimitive)
    assert isinstance(s.primitives[5], AMOutlinePrimitive)
    assert isinstance(s.primitives[6], AMPolygonPrimitive)
    assert isinstance(s.primitives[7], AMMoirePrimitive)
    assert isinstance(s.primitives[8], AMThermalPrimitive)
    assert isinstance(s.primitives[9], AMUnsupportPrimitive)


def testAMParamStmt_conversion():
    name = "POLYGON"
    macro = "5,1,8,25.4,25.4,25.4,0*"
    s = AMParamStmt.from_dict({"param": "AM", "name": name, "macro": macro})

    s.build()
    s.units = "metric"

    # No effect
    s.to_metric()
    assert s.primitives[0].position == (25.4, 25.4)
    assert s.primitives[0].diameter == 25.4

    s.to_inch()
    assert s.units == "inch"
    assert s.primitives[0].position == (1.0, 1.0)
    assert s.primitives[0].diameter == 1.0

    # No effect
    s.to_inch()
    assert s.primitives[0].position == (1.0, 1.0)
    assert s.primitives[0].diameter == 1.0

    macro = "5,1,8,1,1,1,0*"
    s = AMParamStmt.from_dict({"param": "AM", "name": name, "macro": macro})
    s.build()
    s.units = "inch"

    # No effect
    s.to_inch()
    assert s.primitives[0].position == (1.0, 1.0)
    assert s.primitives[0].diameter == 1.0

    s.to_metric()
    assert s.units == "metric"
    assert s.primitives[0].position == (25.4, 25.4)
    assert s.primitives[0].diameter == 25.4

    # No effect
    s.to_metric()
    assert s.primitives[0].position == (25.4, 25.4)
    assert s.primitives[0].diameter == 25.4


def test_AMParamStmt_dump():
    name = "POLYGON"
    macro = "5,1,8,25.4,25.4,25.4,0.0"
    s = AMParamStmt.from_dict({"param": "AM", "name": name, "macro": macro})
    s.build()
    assert s.to_gerber() == "%AMPOLYGON*5,1,8,25.4,25.4,25.4,0.0*%"

    # TODO - Store Equations and update on unit change...
    s = AMParamStmt.from_dict(
        {"param": "AM", "name": "OC8", "macro": "5,1,8,0,0,1.08239X$1,22.5"}
    )
    s.build()
    # assert_equal(s.to_gerber(), '%AMOC8*5,1,8,0,0,1.08239X$1,22.5*%')
    assert s.to_gerber() == "%AMOC8*5,1,8,0,0,0,22.5*%"


def test_AMParamStmt_string():
    name = "POLYGON"
    macro = "5,1,8,25.4,25.4,25.4,0*"
    s = AMParamStmt.from_dict({"param": "AM", "name": name, "macro": macro})
    s.build()
    assert str(s) == "<Aperture Macro POLYGON: 5,1,8,25.4,25.4,25.4,0*>"


def test_ASParamStmt_factory():
    stmt = {"param": "AS", "mode": "AXBY"}
    s = ASParamStmt.from_dict(stmt)
    assert s.param == "AS"
    assert s.mode == "AXBY"


def test_ASParamStmt_dump():
    stmt = {"param": "AS", "mode": "AXBY"}
    s = ASParamStmt.from_dict(stmt)
    assert s.to_gerber() == "%ASAXBY*%"


def test_ASParamStmt_string():
    stmt = {"param": "AS", "mode": "AXBY"}
    s = ASParamStmt.from_dict(stmt)
    assert str(s) == "<Axis Select: AXBY>"


def test_INParamStmt_factory():
    """ Test INParamStmt factory
    """
    stmt = {"param": "IN", "name": "test"}
    inp = INParamStmt.from_dict(stmt)
    assert inp.name == "test"


def test_INParamStmt_dump():
    """ Test INParamStmt to_gerber()
    """
    stmt = {"param": "IN", "name": "test"}
    inp = INParamStmt.from_dict(stmt)
    assert inp.to_gerber() == "%INtest*%"


def test_INParamStmt_string():
    stmt = {"param": "IN", "name": "test"}
    inp = INParamStmt.from_dict(stmt)
    assert str(inp) == "<Image Name: test>"


def test_LNParamStmt_factory():
    """ Test LNParamStmt factory
    """
    stmt = {"param": "LN", "name": "test"}
    lnp = LNParamStmt.from_dict(stmt)
    assert lnp.name == "test"


def test_LNParamStmt_dump():
    """ Test LNParamStmt to_gerber()
    """
    stmt = {"param": "LN", "name": "test"}
    lnp = LNParamStmt.from_dict(stmt)
    assert lnp.to_gerber() == "%LNtest*%"


def test_LNParamStmt_string():
    stmt = {"param": "LN", "name": "test"}
    lnp = LNParamStmt.from_dict(stmt)
    assert str(lnp) == "<Level Name: test>"


def test_comment_stmt():
    """ Test comment statement
    """
    stmt = CommentStmt("A comment")
    assert stmt.type == "COMMENT"
    assert stmt.comment == "A comment"


def test_comment_stmt_dump():
    """ Test CommentStmt to_gerber()
    """
    stmt = CommentStmt("A comment")
    assert stmt.to_gerber() == "G04A comment*"


def test_comment_stmt_string():
    stmt = CommentStmt("A comment")
    assert str(stmt) == "<Comment: A comment>"


def test_eofstmt():
    """ Test EofStmt
    """
    stmt = EofStmt()
    assert stmt.type == "EOF"


def test_eofstmt_dump():
    """ Test EofStmt to_gerber()
    """
    stmt = EofStmt()
    assert stmt.to_gerber() == "M02*"


def test_eofstmt_string():
    assert str(EofStmt()) == "<EOF Statement>"


def test_quadmodestmt_factory():
    """ Test QuadrantModeStmt.from_gerber()
    """
    line = "G74*"
    stmt = QuadrantModeStmt.from_gerber(line)
    assert stmt.type == "QuadrantMode"
    assert stmt.mode == "single-quadrant"

    line = "G75*"
    stmt = QuadrantModeStmt.from_gerber(line)
    assert stmt.mode == "multi-quadrant"


def test_quadmodestmt_validation():
    """ Test QuadrantModeStmt input validation
    """
    line = "G76*"
    pytest.raises(ValueError, QuadrantModeStmt.from_gerber, line)
    pytest.raises(ValueError, QuadrantModeStmt, "quadrant-ful")


def test_quadmodestmt_dump():
    """ Test QuadrantModeStmt.to_gerber()
    """
    for line in ("G74*", "G75*"):
        stmt = QuadrantModeStmt.from_gerber(line)
        assert stmt.to_gerber() == line


def test_regionmodestmt_factory():
    """ Test RegionModeStmt.from_gerber()
    """
    line = "G36*"
    stmt = RegionModeStmt.from_gerber(line)
    assert stmt.type == "RegionMode"
    assert stmt.mode == "on"

    line = "G37*"
    stmt = RegionModeStmt.from_gerber(line)
    assert stmt.mode == "off"


def test_regionmodestmt_validation():
    """ Test RegionModeStmt input validation
    """
    line = "G38*"
    pytest.raises(ValueError, RegionModeStmt.from_gerber, line)
    pytest.raises(ValueError, RegionModeStmt, "off-ish")


def test_regionmodestmt_dump():
    """ Test RegionModeStmt.to_gerber()
    """
    for line in ("G36*", "G37*"):
        stmt = RegionModeStmt.from_gerber(line)
        assert stmt.to_gerber() == line


def test_unknownstmt():
    """ Test UnknownStmt
    """
    line = "G696969*"
    stmt = UnknownStmt(line)
    assert stmt.type == "UNKNOWN"
    assert stmt.line == line


def test_unknownstmt_dump():
    """ Test UnknownStmt.to_gerber()
    """
    lines = ("G696969*", "M03*")
    for line in lines:
        stmt = UnknownStmt(line)
        assert stmt.to_gerber() == line


def test_statement_string():
    """ Test Statement.__str__()
    """
    stmt = Statement("PARAM")
    assert "type=PARAM" in str(stmt)
    stmt.test = "PASS"
    assert "test=PASS" in str(stmt)
    assert "type=PARAM" in str(stmt)


def test_ADParamStmt_factory():
    """ Test ADParamStmt factory
    """
    stmt = {"param": "AD", "d": 0, "shape": "C"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.d == 0
    assert ad.shape == "C"

    stmt = {"param": "AD", "d": 1, "shape": "R"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.d == 1
    assert ad.shape == "R"

    stmt = {"param": "AD", "d": 1, "shape": "C", "modifiers": "1.42"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.d == 1
    assert ad.shape == "C"
    assert ad.modifiers == [(1.42,)]

    stmt = {"param": "AD", "d": 1, "shape": "C", "modifiers": "1.42X"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.d == 1
    assert ad.shape == "C"
    assert ad.modifiers == [(1.42,)]

    stmt = {"param": "AD", "d": 1, "shape": "R", "modifiers": "1.42X1.24"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.d == 1
    assert ad.shape == "R"
    assert ad.modifiers == [(1.42, 1.24)]


def test_ADParamStmt_conversion():
    stmt = {"param": "AD", "d": 0, "shape": "C", "modifiers": "25.4X25.4,25.4X25.4"}
    ad = ADParamStmt.from_dict(stmt)
    ad.units = "metric"

    # No effect
    ad.to_metric()
    assert ad.modifiers[0] == (25.4, 25.4)
    assert ad.modifiers[1] == (25.4, 25.4)

    ad.to_inch()
    assert ad.units == "inch"
    assert ad.modifiers[0] == (1.0, 1.0)
    assert ad.modifiers[1] == (1.0, 1.0)

    # No effect
    ad.to_inch()
    assert ad.modifiers[0] == (1.0, 1.0)
    assert ad.modifiers[1] == (1.0, 1.0)

    stmt = {"param": "AD", "d": 0, "shape": "C", "modifiers": "1X1,1X1"}
    ad = ADParamStmt.from_dict(stmt)
    ad.units = "inch"

    # No effect
    ad.to_inch()
    assert ad.modifiers[0] == (1.0, 1.0)
    assert ad.modifiers[1] == (1.0, 1.0)

    ad.to_metric()
    assert ad.modifiers[0] == (25.4, 25.4)
    assert ad.modifiers[1] == (25.4, 25.4)

    # No effect
    ad.to_metric()
    assert ad.modifiers[0] == (25.4, 25.4)
    assert ad.modifiers[1] == (25.4, 25.4)


def test_ADParamStmt_dump():
    stmt = {"param": "AD", "d": 0, "shape": "C"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.to_gerber() == "%ADD0C*%"
    stmt = {"param": "AD", "d": 0, "shape": "C", "modifiers": "1X1,1X1"}
    ad = ADParamStmt.from_dict(stmt)
    assert ad.to_gerber() == "%ADD0C,1X1,1X1*%"


def test_ADPamramStmt_string():
    stmt = {"param": "AD", "d": 0, "shape": "C"}
    ad = ADParamStmt.from_dict(stmt)
    assert str(ad) == "<Aperture Definition: 0: circle>"

    stmt = {"param": "AD", "d": 0, "shape": "R"}
    ad = ADParamStmt.from_dict(stmt)
    assert str(ad) == "<Aperture Definition: 0: rectangle>"

    stmt = {"param": "AD", "d": 0, "shape": "O"}
    ad = ADParamStmt.from_dict(stmt)
    assert str(ad) == "<Aperture Definition: 0: obround>"

    stmt = {"param": "AD", "d": 0, "shape": "test"}
    ad = ADParamStmt.from_dict(stmt)
    assert str(ad) == "<Aperture Definition: 0: test>"


def test_MIParamStmt_factory():
    stmt = {"param": "MI", "a": 1, "b": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert mi.a == 1
    assert mi.b == 1


def test_MIParamStmt_dump():
    stmt = {"param": "MI", "a": 1, "b": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert mi.to_gerber() == "%MIA1B1*%"
    stmt = {"param": "MI", "a": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert mi.to_gerber() == "%MIA1B0*%"
    stmt = {"param": "MI", "b": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert mi.to_gerber() == "%MIA0B1*%"


def test_MIParamStmt_string():
    stmt = {"param": "MI", "a": 1, "b": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert str(mi) == "<Image Mirror: A=1 B=1>"

    stmt = {"param": "MI", "b": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert str(mi) == "<Image Mirror: A=0 B=1>"

    stmt = {"param": "MI", "a": 1}
    mi = MIParamStmt.from_dict(stmt)
    assert str(mi) == "<Image Mirror: A=1 B=0>"


def test_coordstmt_ctor():
    cs = CoordStmt("G04", 0.0, 0.1, 0.2, 0.3, "D01", FileSettings())
    assert cs.function == "G04"
    assert cs.x == 0.0
    assert cs.y == 0.1
    assert cs.i == 0.2
    assert cs.j == 0.3
    assert cs.op == "D01"


def test_coordstmt_factory():
    stmt = {
        "function": "G04",
        "x": "0",
        "y": "001",
        "i": "002",
        "j": "003",
        "op": "D01",
    }
    cs = CoordStmt.from_dict(stmt, FileSettings())
    assert cs.function == "G04"
    assert cs.x == 0.0
    assert cs.y == 0.1
    assert cs.i == 0.2
    assert cs.j == 0.3
    assert cs.op == "D01"


def test_coordstmt_dump():
    cs = CoordStmt("G04", 0.0, 0.1, 0.2, 0.3, "D01", FileSettings())
    assert cs.to_gerber(FileSettings()) == "G04X0Y001I002J003D01*"


def test_coordstmt_conversion():
    cs = CoordStmt("G71", 25.4, 25.4, 25.4, 25.4, "D01", FileSettings())
    cs.units = "metric"

    # No effect
    cs.to_metric()
    assert cs.x == 25.4
    assert cs.y == 25.4
    assert cs.i == 25.4
    assert cs.j == 25.4
    assert cs.function == "G71"

    cs.to_inch()
    assert cs.units == "inch"
    assert cs.x == 1.0
    assert cs.y == 1.0
    assert cs.i == 1.0
    assert cs.j == 1.0
    assert cs.function == "G70"

    # No effect
    cs.to_inch()
    assert cs.x == 1.0
    assert cs.y == 1.0
    assert cs.i == 1.0
    assert cs.j == 1.0
    assert cs.function == "G70"

    cs = CoordStmt("G70", 1.0, 1.0, 1.0, 1.0, "D01", FileSettings())
    cs.units = "inch"

    # No effect
    cs.to_inch()
    assert cs.x == 1.0
    assert cs.y == 1.0
    assert cs.i == 1.0
    assert cs.j == 1.0
    assert cs.function == "G70"

    cs.to_metric()
    assert cs.x == 25.4
    assert cs.y == 25.4
    assert cs.i == 25.4
    assert cs.j == 25.4
    assert cs.function == "G71"

    # No effect
    cs.to_metric()
    assert cs.x == 25.4
    assert cs.y == 25.4
    assert cs.i == 25.4
    assert cs.j == 25.4
    assert cs.function == "G71"


def test_coordstmt_offset():
    c = CoordStmt("G71", 0, 0, 0, 0, "D01", FileSettings())
    c.offset(1, 0)
    assert c.x == 1.0
    assert c.y == 0.0
    assert c.i == 1.0
    assert c.j == 0.0
    c.offset(0, 1)
    assert c.x == 1.0
    assert c.y == 1.0
    assert c.i == 1.0
    assert c.j == 1.0


def test_coordstmt_string():
    cs = CoordStmt("G04", 0, 1, 2, 3, "D01", FileSettings())
    assert (
        str(cs) == "<Coordinate Statement: Fn: G04 X: 0 Y: 1 I: 2 J: 3 Op: Lights On>"
    )
    cs = CoordStmt("G04", None, None, None, None, "D02", FileSettings())
    assert str(cs) == "<Coordinate Statement: Fn: G04 Op: Lights Off>"
    cs = CoordStmt("G04", None, None, None, None, "D03", FileSettings())
    assert str(cs) == "<Coordinate Statement: Fn: G04 Op: Flash>"
    cs = CoordStmt("G04", None, None, None, None, "TEST", FileSettings())
    assert str(cs) == "<Coordinate Statement: Fn: G04 Op: TEST>"


def test_aperturestmt_ctor():
    ast = ApertureStmt(3, False)
    assert ast.d == 3
    assert ast.deprecated == False
    ast = ApertureStmt(4, True)
    assert ast.d == 4
    assert ast.deprecated == True
    ast = ApertureStmt(4, 1)
    assert ast.d == 4
    assert ast.deprecated == True
    ast = ApertureStmt(3)
    assert ast.d == 3
    assert ast.deprecated == False


def test_aperturestmt_dump():
    ast = ApertureStmt(3, False)
    assert ast.to_gerber() == "D3*"
    ast = ApertureStmt(3, True)
    assert ast.to_gerber() == "G54D3*"
    assert str(ast) == "<Aperture: 3>"
