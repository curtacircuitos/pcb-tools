#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import assert_equal, assert_raises
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
    """ Test CoordinateStmt factory method
    """
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
    """ Test CoordinateStmt to_excellon()
    """
    lines = ['X0278207Y0065293', 'X0243795', 'Y0082528', 'Y0086028',
             'X0251295Y0081528', 'X02525Y0078', 'X0255Y00575', 'Y0052',
             'X02675', 'Y00575', 'X02425', 'Y0052', 'X023', ]
    for line in lines:
        stmt = CoordinateStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_commentstmt_factory():
    """ Test CommentStmt factory method
    """
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
    """ Test CommentStmt to_excellon()
    """
    lines = [';Layer_Color=9474304', ';FILE_FORMAT=2:5', ';TYPE=PLATED', ]
    for line in lines:
        stmt = CommentStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_unitstmt_factory():
    """ Test UnitStmt factory method
    """
    line = 'INCH,LZ'
    stmt = UnitStmt.from_excellon(line)
    assert_equal(stmt.units, 'inch')
    assert_equal(stmt.zero_suppression, 'trailing')

    line = 'METRIC,TZ'
    stmt = UnitStmt.from_excellon(line)
    assert_equal(stmt.units, 'metric')
    assert_equal(stmt.zero_suppression, 'leading')


def test_unitstmt_dump():
    """ Test UnitStmt to_excellon()
    """
    lines = ['INCH,LZ', 'INCH,TZ', 'METRIC,LZ', 'METRIC,TZ', ]
    for line in lines:
        stmt = UnitStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_incrementalmode_factory():
    """ Test IncrementalModeStmt factory method
    """
    line = 'ICI,ON'
    stmt = IncrementalModeStmt.from_excellon(line)
    assert_equal(stmt.mode, 'on')

    line = 'ICI,OFF'
    stmt = IncrementalModeStmt.from_excellon(line)
    assert_equal(stmt.mode, 'off')


def test_incrementalmode_dump():
    """ Test IncrementalModeStmt to_excellon()
    """
    lines = ['ICI,ON', 'ICI,OFF', ]
    for line in lines:
        stmt = IncrementalModeStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_incrementalmode_validation():
    """ Test IncrementalModeStmt input validation
    """
    assert_raises(ValueError, IncrementalModeStmt, 'OFF-ISH')


def test_versionstmt_factory():
    """ Test VersionStmt factory method
    """
    line = 'VER,1'
    stmt = VersionStmt.from_excellon(line)
    assert_equal(stmt.version, 1)

    line = 'VER,2'
    stmt = VersionStmt.from_excellon(line)
    assert_equal(stmt.version, 2)


def test_versionstmt_dump():
    """ Test VersionStmt to_excellon()
    """
    lines = ['VER,1', 'VER,2', ]
    for line in lines:
        stmt = VersionStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)

def test_versionstmt_validation():
    """ Test VersionStmt input validation
    """
    assert_raises(ValueError, VersionStmt, 3)


def test_formatstmt_factory():
    """ Test FormatStmt factory method
    """
    line = 'FMAT,1'
    stmt = FormatStmt.from_excellon(line)
    assert_equal(stmt.format, 1)

    line = 'FMAT,2'
    stmt = FormatStmt.from_excellon(line)
    assert_equal(stmt.format, 2)


def test_formatstmt_dump():
    """ Test FormatStmt to_excellon()
    """
    lines = ['FMAT,1', 'FMAT,2', ]
    for line in lines:
        stmt = FormatStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_formatstmt_validation():
    """ Test FormatStmt input validation
    """
    assert_raises(ValueError, FormatStmt, 3)


def test_linktoolstmt_factory():
    """ Test LinkToolStmt factory method
    """
    line = '1/2/3/4'
    stmt = LinkToolStmt.from_excellon(line)
    assert_equal(stmt.linked_tools, [1, 2, 3, 4])

    line = '01/02/03/04'
    stmt = LinkToolStmt.from_excellon(line)
    assert_equal(stmt.linked_tools, [1, 2, 3, 4])


def test_linktoolstmt_dump():
    """ Test LinkToolStmt to_excellon()
    """
    lines = ['1/2/3/4', '5/6/7', ]
    for line in lines:
        stmt = LinkToolStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_measmodestmt_factory():
    """ Test MeasuringModeStmt factory method
    """
    line = 'M72'
    stmt = MeasuringModeStmt.from_excellon(line)
    assert_equal(stmt.units, 'inch')

    line = 'M71'
    stmt = MeasuringModeStmt.from_excellon(line)
    assert_equal(stmt.units, 'metric')


def test_measmodestmt_dump():
    """ Test MeasuringModeStmt to_excellon()
    """
    lines = ['M71', 'M72', ]
    for line in lines:
        stmt = MeasuringModeStmt.from_excellon(line)
        assert_equal(stmt.to_excellon(), line)


def test_measmodestmt_validation():
    """ Test MeasuringModeStmt input validation
    """
    assert_raises(ValueError, MeasuringModeStmt.from_excellon, 'M70')
    assert_raises(ValueError, MeasuringModeStmt, 'millimeters')
