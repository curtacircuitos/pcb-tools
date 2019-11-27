#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

import pytest
from ..excellon_statements import *
from ..cam import FileSettings


def test_excellon_statement_implementation():
    stmt = ExcellonStatement()
    pytest.raises(NotImplementedError, stmt.from_excellon, None)
    pytest.raises(NotImplementedError, stmt.to_excellon)


def test_excellontstmt():
    """ Smoke test ExcellonStatement
    """
    stmt = ExcellonStatement()
    stmt.to_inch()
    stmt.to_metric()
    stmt.offset()


def test_excellontool_factory():
    """ Test ExcellonTool factory methods
    """
    exc_line = "T8F01B02S00003H04Z05C0.12500"
    settings = FileSettings(
        format=(2, 5), zero_suppression="trailing", units="inch", notation="absolute"
    )
    tool = ExcellonTool.from_excellon(exc_line, settings)
    assert tool.number == 8
    assert tool.diameter == 0.125
    assert tool.feed_rate == 1
    assert tool.retract_rate == 2
    assert tool.rpm == 3
    assert tool.max_hit_count == 4
    assert tool.depth_offset == 5

    stmt = {
        "number": 8,
        "feed_rate": 1,
        "retract_rate": 2,
        "rpm": 3,
        "diameter": 0.125,
        "max_hit_count": 4,
        "depth_offset": 5,
    }
    tool = ExcellonTool.from_dict(settings, stmt)
    assert tool.number == 8
    assert tool.diameter == 0.125
    assert tool.feed_rate == 1
    assert tool.retract_rate == 2
    assert tool.rpm == 3
    assert tool.max_hit_count == 4
    assert tool.depth_offset == 5


def test_excellontool_dump():
    """ Test ExcellonTool to_excellon()
    """
    exc_lines = [
        "T01F0S0C0.01200",
        "T02F0S0C0.01500",
        "T03F0S0C0.01968",
        "T04F0S0C0.02800",
        "T05F0S0C0.03300",
        "T06F0S0C0.03800",
        "T07F0S0C0.04300",
        "T08F0S0C0.12500",
        "T09F0S0C0.13000",
        "T08B01F02H03S00003C0.12500Z04",
        "T01F0S300.999C0.01200",
    ]
    settings = FileSettings(
        format=(2, 5), zero_suppression="trailing", units="inch", notation="absolute"
    )
    for line in exc_lines:
        tool = ExcellonTool.from_excellon(line, settings)
        assert tool.to_excellon() == line


def test_excellontool_order():
    settings = FileSettings(
        format=(2, 5), zero_suppression="trailing", units="inch", notation="absolute"
    )
    line = "T8F00S00C0.12500"
    tool1 = ExcellonTool.from_excellon(line, settings)
    line = "T8C0.12500F00S00"
    tool2 = ExcellonTool.from_excellon(line, settings)
    assert tool1.diameter == tool2.diameter
    assert tool1.feed_rate == tool2.feed_rate
    assert tool1.rpm == tool2.rpm


def test_excellontool_conversion():
    tool = ExcellonTool.from_dict(
        FileSettings(units="metric"), {"number": 8, "diameter": 25.4}
    )
    tool.to_inch()
    assert tool.diameter == 1.0
    tool = ExcellonTool.from_dict(
        FileSettings(units="inch"), {"number": 8, "diameter": 1.0}
    )
    tool.to_metric()
    assert tool.diameter == 25.4

    # Shouldn't change units if we're already using target units
    tool = ExcellonTool.from_dict(
        FileSettings(units="inch"), {"number": 8, "diameter": 25.4}
    )
    tool.to_inch()
    assert tool.diameter == 25.4
    tool = ExcellonTool.from_dict(
        FileSettings(units="metric"), {"number": 8, "diameter": 1.0}
    )
    tool.to_metric()
    assert tool.diameter == 1.0


def test_excellontool_repr():
    tool = ExcellonTool.from_dict(FileSettings(), {"number": 8, "diameter": 0.125})
    assert str(tool) == "<ExcellonTool 08: 0.125in. dia.>"
    tool = ExcellonTool.from_dict(
        FileSettings(units="metric"), {"number": 8, "diameter": 0.125}
    )
    assert str(tool) == "<ExcellonTool 08: 0.125mm dia.>"


def test_excellontool_equality():
    t = ExcellonTool.from_dict(FileSettings(), {"number": 8, "diameter": 0.125})
    t1 = ExcellonTool.from_dict(FileSettings(), {"number": 8, "diameter": 0.125})
    assert t == t1
    t1 = ExcellonTool.from_dict(
        FileSettings(units="metric"), {"number": 8, "diameter": 0.125}
    )
    assert t != t1


def test_toolselection_factory():
    """ Test ToolSelectionStmt factory method
    """
    stmt = ToolSelectionStmt.from_excellon("T01")
    assert stmt.tool == 1
    assert stmt.compensation_index == None
    stmt = ToolSelectionStmt.from_excellon("T0223")
    assert stmt.tool == 2
    assert stmt.compensation_index == 23
    stmt = ToolSelectionStmt.from_excellon("T042")
    assert stmt.tool == 42
    assert stmt.compensation_index == None


def test_toolselection_dump():
    """ Test ToolSelectionStmt to_excellon()
    """
    lines = ["T01", "T0223", "T10", "T09", "T0000"]
    for line in lines:
        stmt = ToolSelectionStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_z_axis_infeed_rate_factory():
    """ Test ZAxisInfeedRateStmt factory method
    """
    stmt = ZAxisInfeedRateStmt.from_excellon("F01")
    assert stmt.rate == 1
    stmt = ZAxisInfeedRateStmt.from_excellon("F2")
    assert stmt.rate == 2
    stmt = ZAxisInfeedRateStmt.from_excellon("F03")
    assert stmt.rate == 3


def test_z_axis_infeed_rate_dump():
    """ Test ZAxisInfeedRateStmt to_excellon()
    """
    inputs = [("F01", "F01"), ("F2", "F02"), ("F00003", "F03")]
    for input_rate, expected_output in inputs:
        stmt = ZAxisInfeedRateStmt.from_excellon(input_rate)
        assert stmt.to_excellon() == expected_output


def test_coordinatestmt_factory():
    """ Test CoordinateStmt factory method
    """
    settings = FileSettings(
        format=(2, 5), zero_suppression="trailing", units="inch", notation="absolute"
    )

    line = "X0278207Y0065293"
    stmt = CoordinateStmt.from_excellon(line, settings)
    assert stmt.x == 2.78207
    assert stmt.y == 0.65293

    # line = 'X02945'
    # stmt = CoordinateStmt.from_excellon(line)
    # assert_equal(stmt.x, 2.945)

    # line = 'Y00575'
    # stmt = CoordinateStmt.from_excellon(line)
    # assert_equal(stmt.y, 0.575)

    settings = FileSettings(
        format=(2, 4), zero_suppression="leading", units="inch", notation="absolute"
    )

    line = "X9660Y4639"
    stmt = CoordinateStmt.from_excellon(line, settings)
    assert stmt.x == 0.9660
    assert stmt.y == 0.4639
    assert stmt.to_excellon(settings) == "X9660Y4639"
    assert stmt.units == "inch"

    settings.units = "metric"
    stmt = CoordinateStmt.from_excellon(line, settings)
    assert stmt.units == "metric"


def test_coordinatestmt_dump():
    """ Test CoordinateStmt to_excellon()
    """
    lines = [
        "X278207Y65293",
        "X243795",
        "Y82528",
        "Y86028",
        "X251295Y81528",
        "X2525Y78",
        "X255Y575",
        "Y52",
        "X2675",
        "Y575",
        "X2425",
        "Y52",
        "X23",
    ]
    settings = FileSettings(
        format=(2, 4), zero_suppression="leading", units="inch", notation="absolute"
    )
    for line in lines:
        stmt = CoordinateStmt.from_excellon(line, settings)
        assert stmt.to_excellon(settings) == line


def test_coordinatestmt_conversion():

    settings = FileSettings()
    settings.units = "metric"
    stmt = CoordinateStmt.from_excellon("X254Y254", settings)

    # No effect
    stmt.to_metric()
    assert stmt.x == 25.4
    assert stmt.y == 25.4

    stmt.to_inch()
    assert stmt.units == "inch"
    assert stmt.x == 1.0
    assert stmt.y == 1.0

    # No effect
    stmt.to_inch()
    assert stmt.x == 1.0
    assert stmt.y == 1.0

    settings.units = "inch"
    stmt = CoordinateStmt.from_excellon("X01Y01", settings)

    # No effect
    stmt.to_inch()
    assert stmt.x == 1.0
    assert stmt.y == 1.0

    stmt.to_metric()
    assert stmt.units == "metric"
    assert stmt.x == 25.4
    assert stmt.y == 25.4

    # No effect
    stmt.to_metric()
    assert stmt.x == 25.4
    assert stmt.y == 25.4


def test_coordinatestmt_offset():
    stmt = CoordinateStmt.from_excellon("X01Y01", FileSettings())
    stmt.offset()
    assert stmt.x == 1
    assert stmt.y == 1
    stmt.offset(1, 0)
    assert stmt.x == 2.0
    assert stmt.y == 1.0
    stmt.offset(0, 1)
    assert stmt.x == 2.0
    assert stmt.y == 2.0


def test_coordinatestmt_string():
    settings = FileSettings(
        format=(2, 4), zero_suppression="leading", units="inch", notation="absolute"
    )
    stmt = CoordinateStmt.from_excellon("X9660Y4639", settings)
    assert str(stmt) == "<Coordinate Statement: X: 0.966 Y: 0.4639 >"


def test_repeathole_stmt_factory():
    stmt = RepeatHoleStmt.from_excellon(
        "R0004X015Y32", FileSettings(zeros="leading", units="inch")
    )
    assert stmt.count == 4
    assert stmt.xdelta == 1.5
    assert stmt.ydelta == 32
    assert stmt.units == "inch"

    stmt = RepeatHoleStmt.from_excellon(
        "R0004X015Y32", FileSettings(zeros="leading", units="metric")
    )
    assert stmt.units == "metric"


def test_repeatholestmt_dump():
    line = "R4X015Y32"
    stmt = RepeatHoleStmt.from_excellon(line, FileSettings())
    assert stmt.to_excellon(FileSettings()) == line


def test_repeatholestmt_conversion():
    line = "R4X0254Y254"
    settings = FileSettings()
    settings.units = "metric"
    stmt = RepeatHoleStmt.from_excellon(line, settings)

    # No effect
    stmt.to_metric()
    assert stmt.xdelta == 2.54
    assert stmt.ydelta == 25.4

    stmt.to_inch()
    assert stmt.units == "inch"
    assert stmt.xdelta == 0.1
    assert stmt.ydelta == 1.0

    # no effect
    stmt.to_inch()
    assert stmt.xdelta == 0.1
    assert stmt.ydelta == 1.0

    line = "R4X01Y1"
    settings.units = "inch"
    stmt = RepeatHoleStmt.from_excellon(line, settings)

    # no effect
    stmt.to_inch()
    assert stmt.xdelta == 1.0
    assert stmt.ydelta == 10.0

    stmt.to_metric()
    assert stmt.units == "metric"
    assert stmt.xdelta == 25.4
    assert stmt.ydelta == 254.0

    # No effect
    stmt.to_metric()
    assert stmt.xdelta == 25.4
    assert stmt.ydelta == 254.0


def test_repeathole_str():
    stmt = RepeatHoleStmt.from_excellon("R4X015Y32", FileSettings())
    assert str(stmt) == "<Repeat Hole: 4 times, offset X: 1.5 Y: 32>"


def test_commentstmt_factory():
    """ Test CommentStmt factory method
    """
    line = ";Layer_Color=9474304"
    stmt = CommentStmt.from_excellon(line)
    assert stmt.comment == line[1:]

    line = ";FILE_FORMAT=2:5"
    stmt = CommentStmt.from_excellon(line)
    assert stmt.comment == line[1:]

    line = ";TYPE=PLATED"
    stmt = CommentStmt.from_excellon(line)
    assert stmt.comment == line[1:]


def test_commentstmt_dump():
    """ Test CommentStmt to_excellon()
    """
    lines = [";Layer_Color=9474304", ";FILE_FORMAT=2:5", ";TYPE=PLATED"]
    for line in lines:
        stmt = CommentStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_header_begin_stmt():
    stmt = HeaderBeginStmt()
    assert stmt.to_excellon(None) == "M48"


def test_header_end_stmt():
    stmt = HeaderEndStmt()
    assert stmt.to_excellon(None) == "M95"


def test_rewindstop_stmt():
    stmt = RewindStopStmt()
    assert stmt.to_excellon(None) == "%"


def test_z_axis_rout_position_stmt():
    stmt = ZAxisRoutPositionStmt()
    assert stmt.to_excellon(None) == "M15"


def test_retract_with_clamping_stmt():
    stmt = RetractWithClampingStmt()
    assert stmt.to_excellon(None) == "M16"


def test_retract_without_clamping_stmt():
    stmt = RetractWithoutClampingStmt()
    assert stmt.to_excellon(None) == "M17"


def test_cutter_compensation_off_stmt():
    stmt = CutterCompensationOffStmt()
    assert stmt.to_excellon(None) == "G40"


def test_cutter_compensation_left_stmt():
    stmt = CutterCompensationLeftStmt()
    assert stmt.to_excellon(None) == "G41"


def test_cutter_compensation_right_stmt():
    stmt = CutterCompensationRightStmt()
    assert stmt.to_excellon(None) == "G42"


def test_endofprogramstmt_factory():
    settings = FileSettings(units="inch")
    stmt = EndOfProgramStmt.from_excellon("M30X01Y02", settings)
    assert stmt.x == 1.0
    assert stmt.y == 2.0
    assert stmt.units == "inch"
    settings.units = "metric"
    stmt = EndOfProgramStmt.from_excellon("M30X01", settings)
    assert stmt.x == 1.0
    assert stmt.y == None
    assert stmt.units == "metric"
    stmt = EndOfProgramStmt.from_excellon("M30Y02", FileSettings())
    assert stmt.x == None
    assert stmt.y == 2.0


def test_endofprogramStmt_dump():
    lines = ["M30X01Y02"]
    for line in lines:
        stmt = EndOfProgramStmt.from_excellon(line, FileSettings())
        assert stmt.to_excellon(FileSettings()) == line


def test_endofprogramstmt_conversion():
    settings = FileSettings()
    settings.units = "metric"
    stmt = EndOfProgramStmt.from_excellon("M30X0254Y254", settings)
    # No effect
    stmt.to_metric()
    assert stmt.x == 2.54
    assert stmt.y == 25.4

    stmt.to_inch()
    assert stmt.units == "inch"
    assert stmt.x == 0.1
    assert stmt.y == 1.0

    # No effect
    stmt.to_inch()
    assert stmt.x == 0.1
    assert stmt.y == 1.0

    settings.units = "inch"
    stmt = EndOfProgramStmt.from_excellon("M30X01Y1", settings)

    # No effect
    stmt.to_inch()
    assert stmt.x == 1.0
    assert stmt.y == 10.0

    stmt.to_metric()
    assert stmt.units == "metric"
    assert stmt.x == 25.4
    assert stmt.y == 254.0

    # No effect
    stmt.to_metric()
    assert stmt.x == 25.4
    assert stmt.y == 254.0


def test_endofprogramstmt_offset():
    stmt = EndOfProgramStmt(1, 1)
    stmt.offset()
    assert stmt.x == 1
    assert stmt.y == 1
    stmt.offset(1, 0)
    assert stmt.x == 2.0
    assert stmt.y == 1.0
    stmt.offset(0, 1)
    assert stmt.x == 2.0
    assert stmt.y == 2.0


def test_unitstmt_factory():
    """ Test UnitStmt factory method
    """
    line = "INCH,LZ"
    stmt = UnitStmt.from_excellon(line)
    assert stmt.units == "inch"
    assert stmt.zeros == "leading"

    line = "INCH,TZ"
    stmt = UnitStmt.from_excellon(line)
    assert stmt.units == "inch"
    assert stmt.zeros == "trailing"

    line = "METRIC,LZ"
    stmt = UnitStmt.from_excellon(line)
    assert stmt.units == "metric"
    assert stmt.zeros == "leading"

    line = "METRIC,TZ"
    stmt = UnitStmt.from_excellon(line)
    assert stmt.units == "metric"
    assert stmt.zeros == "trailing"


def test_unitstmt_dump():
    """ Test UnitStmt to_excellon()
    """
    lines = ["INCH,LZ", "INCH,TZ", "METRIC,LZ", "METRIC,TZ"]
    for line in lines:
        stmt = UnitStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_unitstmt_conversion():
    stmt = UnitStmt.from_excellon("METRIC,TZ")
    stmt.to_inch()
    assert stmt.units == "inch"

    stmt = UnitStmt.from_excellon("INCH,TZ")
    stmt.to_metric()
    assert stmt.units == "metric"


def test_incrementalmode_factory():
    """ Test IncrementalModeStmt factory method
    """
    line = "ICI,ON"
    stmt = IncrementalModeStmt.from_excellon(line)
    assert stmt.mode == "on"

    line = "ICI,OFF"
    stmt = IncrementalModeStmt.from_excellon(line)
    assert stmt.mode == "off"


def test_incrementalmode_dump():
    """ Test IncrementalModeStmt to_excellon()
    """
    lines = ["ICI,ON", "ICI,OFF"]
    for line in lines:
        stmt = IncrementalModeStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_incrementalmode_validation():
    """ Test IncrementalModeStmt input validation
    """
    pytest.raises(ValueError, IncrementalModeStmt, "OFF-ISH")


def test_versionstmt_factory():
    """ Test VersionStmt factory method
    """
    line = "VER,1"
    stmt = VersionStmt.from_excellon(line)
    assert stmt.version == 1

    line = "VER,2"
    stmt = VersionStmt.from_excellon(line)
    assert stmt.version == 2


def test_versionstmt_dump():
    """ Test VersionStmt to_excellon()
    """
    lines = ["VER,1", "VER,2"]
    for line in lines:
        stmt = VersionStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_versionstmt_validation():
    """ Test VersionStmt input validation
    """
    pytest.raises(ValueError, VersionStmt, 3)


def test_formatstmt_factory():
    """ Test FormatStmt factory method
    """
    line = "FMAT,1"
    stmt = FormatStmt.from_excellon(line)
    assert stmt.format == 1

    line = "FMAT,2"
    stmt = FormatStmt.from_excellon(line)
    assert stmt.format == 2


def test_formatstmt_dump():
    """ Test FormatStmt to_excellon()
    """
    lines = ["FMAT,1", "FMAT,2"]
    for line in lines:
        stmt = FormatStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_formatstmt_validation():
    """ Test FormatStmt input validation
    """
    pytest.raises(ValueError, FormatStmt, 3)


def test_linktoolstmt_factory():
    """ Test LinkToolStmt factory method
    """
    line = "1/2/3/4"
    stmt = LinkToolStmt.from_excellon(line)
    assert stmt.linked_tools == [1, 2, 3, 4]

    line = "01/02/03/04"
    stmt = LinkToolStmt.from_excellon(line)
    assert stmt.linked_tools == [1, 2, 3, 4]


def test_linktoolstmt_dump():
    """ Test LinkToolStmt to_excellon()
    """
    lines = ["1/2/3/4", "5/6/7"]
    for line in lines:
        stmt = LinkToolStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_measmodestmt_factory():
    """ Test MeasuringModeStmt factory method
    """
    line = "M72"
    stmt = MeasuringModeStmt.from_excellon(line)
    assert stmt.units == "inch"

    line = "M71"
    stmt = MeasuringModeStmt.from_excellon(line)
    assert stmt.units == "metric"


def test_measmodestmt_dump():
    """ Test MeasuringModeStmt to_excellon()
    """
    lines = ["M71", "M72"]
    for line in lines:
        stmt = MeasuringModeStmt.from_excellon(line)
        assert stmt.to_excellon() == line


def test_measmodestmt_validation():
    """ Test MeasuringModeStmt input validation
    """
    pytest.raises(ValueError, MeasuringModeStmt.from_excellon, "M70")
    pytest.raises(ValueError, MeasuringModeStmt, "millimeters")


def test_measmodestmt_conversion():
    line = "M72"
    stmt = MeasuringModeStmt.from_excellon(line)
    assert stmt.units == "inch"
    stmt.to_metric()
    assert stmt.units == "metric"

    line = "M71"
    stmt = MeasuringModeStmt.from_excellon(line)
    assert stmt.units == "metric"
    stmt.to_inch()
    assert stmt.units == "inch"


def test_routemode_stmt():
    stmt = RouteModeStmt()
    assert stmt.to_excellon(FileSettings()) == "G00"


def test_linearmode_stmt():
    stmt = LinearModeStmt()
    assert stmt.to_excellon(FileSettings()) == "G01"


def test_drillmode_stmt():
    stmt = DrillModeStmt()
    assert stmt.to_excellon(FileSettings()) == "G05"


def test_absolutemode_stmt():
    stmt = AbsoluteModeStmt()
    assert stmt.to_excellon(FileSettings()) == "G90"


def test_unknownstmt():
    stmt = UnknownStmt("TEST")
    assert stmt.stmt == "TEST"
    assert str(stmt) == "<Unknown Statement: TEST>"


def test_unknownstmt_dump():
    stmt = UnknownStmt("TEST")
    assert stmt.to_excellon(FileSettings()) == "TEST"
