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
    stmt = {'param': 'OF', 'a': '0.1234567', 'b':'0.1234567'}
    of = OFParamStmt.from_dict(stmt)
    assert_equal(of.a, 0.1234567)
    assert_equal(of.b, 0.1234567)


def test_OFParamStmt_dump():
    """ Test OFParamStmt to_gerber()
    """
    stmt = {'param': 'OF', 'a': '0.1234567', 'b': '0.1234567'}
    of = OFParamStmt.from_dict(stmt)
    assert_equal(of.to_gerber(), '%OFA0.123456B0.123456*%')

