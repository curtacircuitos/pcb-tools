#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
import os
import pytest

from ..cam import FileSettings
from ..excellon import read, detect_excellon_format, ExcellonFile, ExcellonParser
from ..excellon import DrillHit, DrillSlot
from ..excellon_statements import ExcellonTool, RouteModeStmt


NCDRILL_FILE = os.path.join(os.path.dirname(__file__), "resources/ncdrill.DRD")


def test_format_detection():
    """ Test file type detection
    """
    with open(NCDRILL_FILE, "rU") as f:
        data = f.read()
    settings = detect_excellon_format(data)
    assert settings["format"] == (2, 4)
    assert settings["zeros"] == "trailing"

    settings = detect_excellon_format(filename=NCDRILL_FILE)
    assert settings["format"] == (2, 4)
    assert settings["zeros"] == "trailing"


def test_read():
    ncdrill = read(NCDRILL_FILE)
    assert isinstance(ncdrill, ExcellonFile)


def test_write():
    ncdrill = read(NCDRILL_FILE)
    ncdrill.write("test.ncd")
    with open(NCDRILL_FILE, "rU") as src:
        srclines = src.readlines()
    with open("test.ncd", "rU") as res:
        for idx, line in enumerate(res):
            assert line.strip() == srclines[idx].strip()
    os.remove("test.ncd")


def test_read_settings():
    ncdrill = read(NCDRILL_FILE)
    assert ncdrill.settings["format"] == (2, 4)
    assert ncdrill.settings["zeros"] == "trailing"


def test_bounding_box():
    ncdrill = read(NCDRILL_FILE)
    xbound, ybound = ncdrill.bounding_box
    pytest.approx(xbound, (0.1300, 2.1430))
    pytest.approx(ybound, (0.3946, 1.7164))


def test_report():
    ncdrill = read(NCDRILL_FILE)
    rprt = ncdrill.report()


def test_conversion():
    import copy

    ncdrill = read(NCDRILL_FILE)
    assert ncdrill.settings.units == "inch"
    ncdrill_inch = copy.deepcopy(ncdrill)

    ncdrill.to_metric()
    assert ncdrill.settings.units == "metric"
    for tool in iter(ncdrill_inch.tools.values()):
        tool.to_metric()

    for statement in ncdrill_inch.statements:
        statement.to_metric()

    for m_tool, i_tool in zip(
        iter(ncdrill.tools.values()), iter(ncdrill_inch.tools.values())
    ):
        assert i_tool == m_tool

    for m, i in zip(ncdrill.primitives, ncdrill_inch.primitives):

        assert m.position == i.position, "%s not equal to %s" % (m, i)
        assert m.diameter == i.diameter, "%s not equal to %s" % (m, i)


def test_parser_hole_count():
    settings = FileSettings(**detect_excellon_format(NCDRILL_FILE))
    p = ExcellonParser(settings)
    p.parse(NCDRILL_FILE)
    assert p.hole_count == 36


def test_parser_hole_sizes():
    settings = FileSettings(**detect_excellon_format(NCDRILL_FILE))
    p = ExcellonParser(settings)
    p.parse(NCDRILL_FILE)
    assert p.hole_sizes == [0.0236, 0.0354, 0.04, 0.126, 0.128]


def test_parse_whitespace():
    p = ExcellonParser(FileSettings())
    assert p._parse_line("         ") == None


def test_parse_comment():
    p = ExcellonParser(FileSettings())
    p._parse_line(";A comment")
    assert p.statements[0].comment == "A comment"


def test_parse_format_comment():
    p = ExcellonParser(FileSettings())
    p._parse_line("; FILE_FORMAT=9:9 ")
    assert p.format == (9, 9)


def test_parse_header():
    p = ExcellonParser(FileSettings())
    p._parse_line("M48   ")
    assert p.state == "HEADER"
    p._parse_line("M95   ")
    assert p.state == "DRILL"


def test_parse_rout():
    p = ExcellonParser(FileSettings())
    p._parse_line("G00X040944Y019842")
    assert p.state == "ROUT"
    p._parse_line("G05 ")
    assert p.state == "DRILL"


def test_parse_version():
    p = ExcellonParser(FileSettings())
    p._parse_line("VER,1  ")
    assert p.statements[0].version == 1
    p._parse_line("VER,2  ")
    assert p.statements[1].version == 2


def test_parse_format():
    p = ExcellonParser(FileSettings())
    p._parse_line("FMAT,1  ")
    assert p.statements[0].format == 1
    p._parse_line("FMAT,2  ")
    assert p.statements[1].format == 2


def test_parse_units():
    settings = FileSettings(units="inch", zeros="trailing")
    p = ExcellonParser(settings)
    p._parse_line(";METRIC,LZ")
    assert p.units == "inch"
    assert p.zeros == "trailing"
    p._parse_line("METRIC,LZ")
    assert p.units == "metric"
    assert p.zeros == "leading"


def test_parse_incremental_mode():
    settings = FileSettings(units="inch", zeros="trailing")
    p = ExcellonParser(settings)
    assert p.notation == "absolute"
    p._parse_line("ICI,ON  ")
    assert p.notation == "incremental"
    p._parse_line("ICI,OFF  ")
    assert p.notation == "absolute"


def test_parse_absolute_mode():
    settings = FileSettings(units="inch", zeros="trailing")
    p = ExcellonParser(settings)
    assert p.notation == "absolute"
    p._parse_line("ICI,ON  ")
    assert p.notation == "incremental"
    p._parse_line("G90  ")
    assert p.notation == "absolute"


def test_parse_repeat_hole():
    p = ExcellonParser(FileSettings())
    p.active_tool = ExcellonTool(FileSettings(), number=8)
    p._parse_line("R03X1.5Y1.5")
    assert p.statements[0].count == 3


def test_parse_incremental_position():
    p = ExcellonParser(FileSettings(notation="incremental"))
    p._parse_line("X01Y01")
    p._parse_line("X01Y01")
    assert p.pos == [2.0, 2.0]


def test_parse_unknown():
    p = ExcellonParser(FileSettings())
    p._parse_line("Not A Valid Statement")
    assert p.statements[0].stmt == "Not A Valid Statement"


def test_drill_hit_units_conversion():
    """ Test unit conversion for drill hits
    """
    # Inch hit
    settings = FileSettings(units="inch")
    tool = ExcellonTool(settings, diameter=1.0)
    hit = DrillHit(tool, (1.0, 1.0))

    assert hit.tool.settings.units == "inch"
    assert hit.tool.diameter == 1.0
    assert hit.position == (1.0, 1.0)

    # No Effect
    hit.to_inch()

    assert hit.tool.settings.units == "inch"
    assert hit.tool.diameter == 1.0
    assert hit.position == (1.0, 1.0)

    # Should convert
    hit.to_metric()

    assert hit.tool.settings.units == "metric"
    assert hit.tool.diameter == 25.4
    assert hit.position == (25.4, 25.4)

    # No Effect
    hit.to_metric()

    assert hit.tool.settings.units == "metric"
    assert hit.tool.diameter == 25.4
    assert hit.position == (25.4, 25.4)

    # Convert back to inch
    hit.to_inch()

    assert hit.tool.settings.units == "inch"
    assert hit.tool.diameter == 1.0
    assert hit.position == (1.0, 1.0)


def test_drill_hit_offset():
    TEST_VECTORS = [
        ((0.0, 0.0), (0.0, 1.0), (0.0, 1.0)),
        ((0.0, 0.0), (1.0, 1.0), (1.0, 1.0)),
        ((1.0, 1.0), (0.0, -1.0), (1.0, 0.0)),
        ((1.0, 1.0), (-1.0, -1.0), (0.0, 0.0)),
    ]
    for position, offset, expected in TEST_VECTORS:
        settings = FileSettings(units="inch")
        tool = ExcellonTool(settings, diameter=1.0)
        hit = DrillHit(tool, position)

        assert hit.position == position

        hit.offset(offset[0], offset[1])

        assert hit.position == expected


def test_drill_slot_units_conversion():
    """ Test unit conversion for drill hits
    """
    # Inch hit
    settings = FileSettings(units="inch")
    tool = ExcellonTool(settings, diameter=1.0)
    hit = DrillSlot(tool, (1.0, 1.0), (10.0, 10.0), DrillSlot.TYPE_ROUT)

    assert hit.tool.settings.units == "inch"
    assert hit.tool.diameter == 1.0
    assert hit.start == (1.0, 1.0)
    assert hit.end == (10.0, 10.0)

    # No Effect
    hit.to_inch()

    assert hit.tool.settings.units == "inch"
    assert hit.tool.diameter == 1.0
    assert hit.start == (1.0, 1.0)
    assert hit.end == (10.0, 10.0)

    # Should convert
    hit.to_metric()

    assert hit.tool.settings.units == "metric"
    assert hit.tool.diameter == 25.4
    assert hit.start == (25.4, 25.4)
    assert hit.end == (254.0, 254.0)

    # No Effect
    hit.to_metric()

    assert hit.tool.settings.units == "metric"
    assert hit.tool.diameter == 25.4
    assert hit.start == (25.4, 25.4)
    assert hit.end == (254.0, 254.0)

    # Convert back to inch
    hit.to_inch()

    assert hit.tool.settings.units == "inch"
    assert hit.tool.diameter == 1.0
    assert hit.start == (1.0, 1.0)
    assert hit.end == (10.0, 10.0)


def test_drill_slot_offset():
    TEST_VECTORS = [
        ((0.0, 0.0), (1.0, 1.0), (0.0, 0.0), (0.0, 0.0), (1.0, 1.0)),
        ((0.0, 0.0), (1.0, 1.0), (1.0, 0.0), (1.0, 0.0), (2.0, 1.0)),
        ((0.0, 0.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (2.0, 2.0)),
        ((0.0, 0.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0), (0.0, 2.0)),
    ]
    for start, end, offset, expected_start, expected_end in TEST_VECTORS:
        settings = FileSettings(units="inch")
        tool = ExcellonTool(settings, diameter=1.0)
        slot = DrillSlot(tool, start, end, DrillSlot.TYPE_ROUT)

        assert slot.start == start
        assert slot.end == end

        slot.offset(offset[0], offset[1])

        assert slot.start == expected_start
        assert slot.end == expected_end


def test_drill_slot_bounds():
    TEST_VECTORS = [
        ((0.0, 0.0), (1.0, 1.0), 1.0, ((-0.5, 1.5), (-0.5, 1.5))),
        ((0.0, 0.0), (1.0, 1.0), 0.5, ((-0.25, 1.25), (-0.25, 1.25))),
    ]
    for start, end, diameter, expected in TEST_VECTORS:
        settings = FileSettings(units="inch")
        tool = ExcellonTool(settings, diameter=diameter)
        slot = DrillSlot(tool, start, end, DrillSlot.TYPE_ROUT)

        assert slot.bounding_box == expected


def test_handling_multi_line_g00_and_g1():
    """Route Mode statements with coordinates on separate line are handled
    """
    test_data = """
%
M48
M72
T01C0.0236
%
T01
G00
X040944Y019842
M15
G01
X040944Y020708
M16
"""
    uut = ExcellonParser()
    uut.parse_raw(test_data)
    assert (
        len([stmt for stmt in uut.statements if isinstance(stmt, RouteModeStmt)]) == 2
    )
