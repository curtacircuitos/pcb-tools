#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import *
from ..excellon_statements import *


def test_excellontool_factory():
    """ Test ExcellonTool factory method
    """
    exc_line = 'T8F00S00C0.12500'
    settings = {'format': (2, 5), 'zero_suppression': 'trailing',
                'units': 'inch', 'notation': 'absolute'}
    tool = ExcellonTool.from_excellon(exc_line, settings)
    assert_equal(tool.diameter, 0.125)
    assert_equal(tool.feed_rate, 0)
    assert_equal(tool.rpm, 0)


def test_excellontool_dump():
    """ Test ExcellonTool to_excellon()
    """
    exc_lines = ['T1F00S00C0.01200', 'T2F00S00C0.01500', 'T3F00S00C0.01968',
                 'T4F00S00C0.02800', 'T5F00S00C0.03300', 'T6F00S00C0.03800',
                 'T7F00S00C0.04300', 'T8F00S00C0.12500', 'T9F00S00C0.13000', ]
    settings = {'format': (2, 5), 'zero_suppression': 'trailing',
                'units': 'inch', 'notation': 'absolute'}
    for line in exc_lines:
        tool = ExcellonTool.from_excellon(line, settings)
        assert_equal(tool.to_excellon(), line)


def test_excellontool_order():
    settings = {'format': (2, 5), 'zero_suppression': 'trailing',
                'units': 'inch', 'notation': 'absolute'}
    line = 'T8F00S00C0.12500'
    tool1 = ExcellonTool.from_excellon(line, settings)
    line = 'T8C0.12500F00S00'
    tool2 = ExcellonTool.from_excellon(line, settings)
    assert_equal(tool1.diameter, tool2.diameter)
    assert_equal(tool1.feed_rate, tool2.feed_rate)
    assert_equal(tool1.rpm, tool2.rpm)


def test_toolselection_factory():
    """ Test ToolSelectionStmt factory method
    """
    stmt = ToolSelectionStmt.from_excellon('T01')
    assert_equal(stmt.tool, 1)
    assert_equal(stmt.compensation_index, None)
    stmt = ToolSelectionStmt.from_excellon('T0223')
    assert_equal(stmt.tool, 2)
    assert_equal(stmt.compensation_index, 23)


def test_toolselection_dump():
    """ Test ToolSelectionStmt to_excellon()
    """
    lines = ['T01', 'T0223', 'T10', 'T09', 'T0000']
    for line in lines:
        stmt = ToolSelectionStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_coordinatestmt_factory():
    line = 'X0278207Y0065293'
    stmt = CoordinateStmt.from_excellon(line)
    assert_equal(stmt.x, 2.78207)
    assert_equal(stmt.y, 0.65293)

    line = 'X02945'
    stmt = CoordinateStmt.from_excellon(line)
    assert_equal(stmt.x, 2.945)

    line = 'Y00575'
    stmt = CoordinateStmt.from_excellon(line)
    assert_equal(stmt.y, 0.575)


def test_coordinatestmt_dump():
    lines = ['X0278207Y0065293', 'X0243795', 'Y0082528', 'Y0086028',
             'X0251295Y0081528', 'X02525Y0078', 'X0255Y00575', 'Y0052',
             'X02675', 'Y00575', 'X02425', 'Y0052', 'X023', ]
    for line in lines:
        stmt = CoordinateStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_commentstmt_factory():
    line = ';Layer_Color=9474304'
    stmt = CommentStmt.from_excellon(line)
    assert_equal(stmt.comment, line[1:])

    line = ';FILE_FORMAT=2:5'
    stmt = CommentStmt.from_excellon(line)
    assert_equal(stmt.comment, line[1:])

    line = ';TYPE=PLATED'
    stmt = CommentStmt.from_excellon(line)
    assert_equal(stmt.comment, line[1:])


def test_commentstmt_dump():
    lines = [';Layer_Color=9474304', ';FILE_FORMAT=2:5', ';TYPE=PLATED', ]
    for line in lines:
        stmt = CommentStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)

