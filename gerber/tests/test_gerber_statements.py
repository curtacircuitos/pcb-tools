#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import *
from ..gerber_statements import *
from ..cam import FileSettings


def test_FSParamStmt_factory():
    """ Test FSParamStruct factory
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


def test_FSParamStmt():
    """ Test FSParamStmt initialization
    """
    param = 'FS'
    zeros = 'trailing'
    notation = 'absolute'
    fmt = (2, 5)
    stmt = FSParamStmt(param, zeros, notation, fmt)
    assert_equal(stmt.param, param)
    assert_equal(stmt.zero_suppression, zeros)
    assert_equal(stmt.notation, notation)
    assert_equal(stmt.format, fmt)


def test_FSParamStmt_dump():
    """ Test FSParamStmt to_gerber()
    """
    stmt = {'param': 'FS', 'zero': 'L', 'notation': 'A', 'x': '27'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(fs.to_gerber(), '%FSLAX27Y27*%')

    stmt = {'param': 'FS', 'zero': 'T', 'notation': 'I', 'x': '25'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(fs.to_gerber(), '%FSTIX25Y25*%')

    settings = FileSettings(zero_suppression='leading', notation='absolute')
    assert_equal(fs.to_gerber(settings), '%FSLAX25Y25*%')


def test_FSParamStmt_string():
    """ Test FSParamStmt.__str__()
    """
    stmt = {'param': 'FS', 'zero': 'L', 'notation': 'A', 'x': '27'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(str(fs), '<Format Spec: 2:7 leading zero suppression absolute notation>')

    stmt = {'param': 'FS', 'zero': 'T', 'notation': 'I', 'x': '25'}
    fs = FSParamStmt.from_dict(stmt)
    assert_equal(str(fs), '<Format Spec: 2:5 trailing zero suppression incremental notation>')


def test_MOParamStmt_factory():
    """ Test MOParamStruct factory
    """
    stmts = [{'param': 'MO', 'mo': 'IN'}, {'param': 'MO', 'mo': 'in'}, ]
    for stmt in stmts:
        mo = MOParamStmt.from_dict(stmt)
        assert_equal(mo.param, 'MO')
        assert_equal(mo.mode, 'inch')

    stmts = [{'param': 'MO', 'mo': 'MM'}, {'param': 'MO', 'mo': 'mm'}, ]
    for stmt in stmts:
        mo = MOParamStmt.from_dict(stmt)
        assert_equal(mo.param, 'MO')
        assert_equal(mo.mode, 'metric')


def test_MOParamStmt():
    """ Test MOParamStmt initialization
    """
    param = 'MO'
    mode = 'inch'
    stmt = MOParamStmt(param, mode)
    assert_equal(stmt.param, param)

    for mode in ['inch', 'metric']:
        stmt = MOParamStmt(param, mode)
        assert_equal(stmt.mode, mode)


def test_MOParamStmt_dump():
    """ Test MOParamStmt to_gerber()
    """
    stmt = {'param': 'MO', 'mo': 'IN'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(mo.to_gerber(), '%MOIN*%')

    stmt = {'param': 'MO', 'mo': 'MM'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(mo.to_gerber(), '%MOMM*%')


def test_MOParamStmt_string():
    """ Test MOParamStmt.__str__()
    """
    stmt = {'param': 'MO', 'mo': 'IN'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(str(mo), '<Mode: inches>')

    stmt = {'param': 'MO', 'mo': 'MM'}
    mo = MOParamStmt.from_dict(stmt)
    assert_equal(str(mo), '<Mode: millimeters>')


def test_IPParamStmt_factory():
    """ Test IPParamStruct factory
    """
    stmt = {'param': 'IP', 'ip': 'POS'}
    ip = IPParamStmt.from_dict(stmt)
    assert_equal(ip.ip, 'positive')

    stmt = {'param': 'IP', 'ip': 'NEG'}
    ip = IPParamStmt.from_dict(stmt)
    assert_equal(ip.ip, 'negative')


def test_IPParamStmt():
    """ Test IPParamStmt initialization
    """
    param = 'IP'
    for ip in ['positive', 'negative']:
        stmt = IPParamStmt(param, ip)
        assert_equal(stmt.param, param)
        assert_equal(stmt.ip, ip)


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
    """ Test OFParamStmt factory
    """
    stmt = {'param': 'OF', 'a': '0.1234567', 'b': '0.1234567'}
    of = OFParamStmt.from_dict(stmt)
    assert_equal(of.a, 0.1234567)
    assert_equal(of.b, 0.1234567)


def test_OFParamStmt():
    """ Test IPParamStmt initialization
    """
    param = 'OF'
    for val in [0.0, -3.4567]:
        stmt = OFParamStmt(param, val, val)
        assert_equal(stmt.param, param)
        assert_equal(stmt.a, val)
        assert_equal(stmt.b, val)


def test_OFParamStmt_dump():
    """ Test OFParamStmt to_gerber()
    """
    stmt = {'param': 'OF', 'a': '0.123456', 'b': '0.123456'}
    of = OFParamStmt.from_dict(stmt)
    assert_equal(of.to_gerber(), '%OFA0.12345B0.12345*%')


def test_LPParamStmt_factory():
    """ Test LPParamStmt factory
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


def test_LPParamStmt_string():
    """ Test LPParamStmt.__str__()
    """
    stmt = {'param': 'LP', 'lp': 'D'}
    lp = LPParamStmt.from_dict(stmt)
    assert_equal(str(lp), '<Level Polarity: dark>')

    stmt = {'param': 'LP', 'lp': 'C'}
    lp = LPParamStmt.from_dict(stmt)
    assert_equal(str(lp), '<Level Polarity: clear>')


def test_INParamStmt_factory():
    """ Test INParamStmt factory
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
    """ Test LNParamStmt factory
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


def test_statement_string():
    """ Test Statement.__str__()
    """
    stmt = Statement('PARAM')
    assert_equal(str(stmt), '<Statement type=PARAM>')
    stmt.test='PASS'
    assert_equal(str(stmt), '<Statement test=PASS type=PARAM>')


def test_ADParamStmt_factory():
    """ Test ADParamStmt factory
    """
    stmt = {'param': 'AD', 'd': 0, 'shape': 'C'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(ad.d, 0)
    assert_equal(ad.shape, 'C')

    stmt = {'param': 'AD', 'd': 1, 'shape': 'R'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(ad.d, 1)
    assert_equal(ad.shape, 'R')

    stmt = {'param': 'AD', 'd': 2, 'shape': 'O'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(ad.d, 2)
    assert_equal(ad.shape, 'O')


def test_ADParamStmt_dump():
    """ Test ADParamStmt.to_gerber()
    """
    stmt = {'param': 'AD', 'd': 0, 'shape': 'C'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(ad.to_gerber(),'%ADD0C*%')

    stmt = {'param': 'AD', 'd': 1, 'shape': 'R'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(ad.to_gerber(),'%ADD1R*%')

    stmt = {'param': 'AD', 'd': 2, 'shape': 'O'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(ad.to_gerber(),'%ADD2O*%')

def test_ADParamStmt_string():
    """ Test ADParamStmt.__str__()
    """
    stmt = {'param': 'AD', 'd': 0, 'shape': 'C'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(str(ad), '<Aperture Definition: 0: circle>')

    stmt = {'param': 'AD', 'd': 1, 'shape': 'R'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(str(ad), '<Aperture Definition: 1: rectangle>')

    stmt = {'param': 'AD', 'd': 2, 'shape': 'O'}
    ad = ADParamStmt.from_dict(stmt)
    assert_equal(str(ad), '<Aperture Definition: 2: obround')
