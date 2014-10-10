#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import *
from ..gerber_statements import *


def test_FSParamStmt_factory():
    """ Test FSParamStruct factory correctly handles parameters
    """
    stmt = {'param': 'FS', 'zero': 'L', 'notation': 'A', 'x': '27'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(fs.param, 'FS')
    assert_equal(fs.zero_suppression, 'leading')
    assert_equal(fs.notation, 'absolute')
    assert_equal(fs.format, (2, 7))

    stmt = {'param': 'FS', 'zero': 'T', 'notation': 'I', 'x': '27'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(fs.param, 'FS')
    assert_equal(fs.zero_suppression, 'trailing')
    assert_equal(fs.notation, 'incremental')
    assert_equal(fs.format, (2, 7))


def test_FSParamStmt_dump():
    """ Test FSParamStmt to_gerber()
    """
    stmt = {'param': 'FS', 'zero': 'L', 'notation': 'A', 'x': '27'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(fs.to_gerber(), '%FSLAX27Y27*%')

    stmt = {'param': 'FS', 'zero': 'T', 'notation': 'I', 'x': '25'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(fs.to_gerber(), '%FSTIX25Y25*%')


def test_MOParamStmt_factory():
    """ Test MOParamStruct factory correctly handles parameters
    """
    stmt = {'param': 'MO', 'mo': 'IN'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(mo.param, 'MO')
    assert_equal(mo.mode, 'inch')

    stmt = {'param': 'MO', 'mo': 'MM'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(mo.param, 'MO')
    assert_equal(mo.mode, 'metric')


def test_MOParamStmt_dump():
    """ Test MOParamStmt to_gerber()
    """
    stmt = {'param': 'MO', 'mo': 'IN'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(mo.to_gerber(), '%MOIN*%')

    stmt = {'param': 'MO', 'mo': 'MM'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(mo.to_gerber(), '%MOMM*%')


def test_IPParamStmt_factory():
    """ Test IPParamStruct factory correctly handles parameters
    """
    stmt = {'param': 'IP', 'ip': 'POS'}
    ip = IPParamStmt.from_dict(stmt)
    assert_equal(ip.ip, 'positive')

    stmt = {'param': 'IP', 'ip': 'NEG'}
    ip = IPParamStmt.from_dict(stmt)
    assert_equal(ip.ip, 'negative')


def test_IPParamStmt_dump():
    """ Test IPParamStmt to_gerber()
    """
    stmt = {'param': 'IP', 'ip': 'POS'}
    ip = IPParamStmt.from_dict(stmt)
    assert_equal(ip.to_gerber(), '%IPPOS*%')

    stmt = {'param': 'IP', 'ip': 'NEG'}
    ip = IPParamStmt.from_dict(stmt)
    assert_equal(ip.to_gerber(), '%IPNEG*%')


def test_OFParamStmt_factory():
    """ Test OFParamStmt factory correctly handles parameters
    """
    stmt = {'param': 'OF', 'a': '0.1234567', 'b': '0.1234567'}
    of = OFParamStmt.from_dict(stmt)
    assert_equal(of.a, 0.1234567)
    assert_equal(of.b, 0.1234567)


def test_OFParamStmt_dump():
    """ Test OFParamStmt to_gerber()
    """
    stmt = {'param': 'OF', 'a': '0.1234567', 'b': '0.1234567'}
    of = OFParamStmt.from_dict(stmt)
    assert_equal(of.to_gerber(), '%OFA0.123456B0.123456*%')


def test_LPParamStmt_factory():
    """ Test LPParamStmt factory correctly handles parameters
    """
    stmt = {'param': 'LP', 'lp': 'C'}
    lp = LPParamStmt.from_dict(stmt)
    assert_equal(lp.lp, 'clear')

    stmt = {'param': 'LP', 'lp': 'D'}
    lp = LPParamStmt.from_dict(stmt)
    assert_equal(lp.lp, 'dark')

def test_LPParamStmt_dump():
    """ Test LPParamStmt to_gerber()
    """
    stmt = {'param': 'LP', 'lp': 'C'}
    lp = LPParamStmt.from_dict(stmt)
    assert_equal(lp.to_gerber(), '%LPC*%')

    stmt = {'param': 'LP', 'lp': 'D'}
    lp = LPParamStmt.from_dict(stmt)
    assert_equal(lp.to_gerber(), '%LPD*%')


def test_INParamStmt_factory():
    """ Test INParamStmt factory correctly handles parameters
    """
    stmt = {'param': 'IN', 'name': 'test'}
    inp = INParamStmt.from_dict(stmt)
    assert_equal(inp.name, 'test')

def test_INParamStmt_dump():
    """ Test INParamStmt to_gerber()
    """
    stmt = {'param': 'IN', 'name': 'test'}
    inp = INParamStmt.from_dict(stmt)
    assert_equal(inp.to_gerber(), '%INtest*%')


def test_LNParamStmt_factory():
    """ Test LNParamStmt factory correctly handles parameters
    """
    stmt = {'param': 'LN', 'name': 'test'}
    lnp = LNParamStmt.from_dict(stmt)
    assert_equal(lnp.name, 'test')

def test_LNParamStmt_dump():
    """ Test LNParamStmt to_gerber()
    """
    stmt = {'param': 'LN', 'name': 'test'}
    lnp = LNParamStmt.from_dict(stmt)
    assert_equal(lnp.to_gerber(), '%LNtest*%')

def test_comment_stmt():
    """ Test comment statement
    """
    stmt = CommentStmt('A comment')
    assert_equal(stmt.type, 'COMMENT')
    assert_equal(stmt.comment, 'A comment')

def test_comment_stmt_dump():
    """ Test CommentStmt to_gerber()
    """
    stmt = CommentStmt('A comment')
    assert_equal(stmt.to_gerber(), 'G04A comment*')


def test_eofstmt():
    """ Test EofStmt
    """
    stmt = EofStmt()
    assert_equal(stmt.type, 'EOF')

def test_eofstmt_dump():
    """ Test EofStmt to_gerber()
    """
    stmt = EofStmt()
    assert_equal(stmt.to_gerber(), 'M02*')


def test_quadmodestmt_factory():
    """ Test QuadrantModeStmt.from_gerber()
    """
    line = 'G74*'
    stmt = QuadrantModeStmt.from_gerber(line)
    assert_equal(stmt.type, 'QuadrantMode')
    assert_equal(stmt.mode, 'single-quadrant')

    line = 'G75*'
    stmt = QuadrantModeStmt.from_gerber(line)
    assert_equal(stmt.mode, 'multi-quadrant')

def test_quadmodestmt_validation():
    """ Test QuadrantModeStmt input validation
    """
    line = 'G76*'
    assert_raises(ValueError, QuadrantModeStmt.from_gerber, line)
    assert_raises(ValueError, QuadrantModeStmt, 'quadrant-ful')


def test_quadmodestmt_dump():
    """ Test QuadrantModeStmt.to_gerber()
    """
    for line in ('G74*', 'G75*',):
        stmt = QuadrantModeStmt.from_gerber(line)
        assert_equal(stmt.to_gerber(), line)


def test_regionmodestmt_factory():
    """ Test RegionModeStmt.from_gerber()
    """
    line = 'G36*'
    stmt = RegionModeStmt.from_gerber(line)
    assert_equal(stmt.type, 'RegionMode')
    assert_equal(stmt.mode, 'on')

    line = 'G37*'
    stmt = RegionModeStmt.from_gerber(line)
    assert_equal(stmt.mode, 'off')


def test_regionmodestmt_validation():
    """ Test RegionModeStmt input validation
    """
    line = 'G38*'
    assert_raises(ValueError, RegionModeStmt.from_gerber, line)
    assert_raises(ValueError, RegionModeStmt, 'off-ish')


def test_regionmodestmt_dump():
    """ Test RegionModeStmt.to_gerber()
    """
    for line in ('G36*', 'G37*',):
        stmt = RegionModeStmt.from_gerber(line)
        assert_equal(stmt.to_gerber(), line)


def test_unknownstmt():
    """ Test UnknownStmt
    """
    line = 'G696969*'
    stmt = UnknownStmt(line)
    assert_equal(stmt.type, 'UNKNOWN')
    assert_equal(stmt.line, line)


def test_unknownstmt_dump():
    """ Test UnknownStmt.to_gerber()
    """
    lines = ('G696969*', 'M03*',)
    for line in lines:
        stmt = UnknownStmt(line)
        assert_equal(stmt.to_gerber(), line)

