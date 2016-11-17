#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..ipc356 import *
from ..cam import FileSettings
from .tests import *

import os

IPC_D_356_FILE = os.path.join(os.path.dirname(__file__),
                              'resources/ipc-d-356.ipc')


def test_read():
    ipcfile = read(IPC_D_356_FILE)
    assert(isinstance(ipcfile, IPCNetlist))



def test_parser():
    ipcfile = read(IPC_D_356_FILE)
    assert_equal(ipcfile.settings.units, 'inch')
    assert_equal(ipcfile.settings.angle_units, 'degrees')
    assert_equal(len(ipcfile.comments), 3)
    assert_equal(len(ipcfile.parameters), 4)
    assert_equal(len(ipcfile.test_records), 105)
    assert_equal(len(ipcfile.components), 21)
    assert_equal(len(ipcfile.vias), 14)
    assert_equal(ipcfile.test_records[-1].net_name, 'A_REALLY_LONG_NET_NAME')
    assert_equal(ipcfile.outlines[0].type, 'BOARD_EDGE')
    assert_equal(set(ipcfile.outlines[0].points),
                 {(0., 0.), (2.25, 0.), (2.25, 1.5), (0., 1.5), (0.13, 0.024)})


def test_comment():
    c = IPC356_Comment('Layer Stackup:')
    assert_equal(c.comment, 'Layer Stackup:')
    c = IPC356_Comment.from_line('C  Layer Stackup:   ')
    assert_equal(c.comment, 'Layer Stackup:')
    assert_raises(ValueError, IPC356_Comment.from_line, 'P  JOB')
    assert_equal(str(c), '<IPC-D-356 Comment: Layer Stackup:>')


def test_parameter():
    p = IPC356_Parameter('VER', 'IPC-D-356A')
    assert_equal(p.parameter, 'VER')
    assert_equal(p.value, 'IPC-D-356A')
    p = IPC356_Parameter.from_line('P  VER IPC-D-356A    ')
    assert_equal(p.parameter, 'VER')
    assert_equal(p.value, 'IPC-D-356A')
    assert_raises(ValueError, IPC356_Parameter.from_line,
                  'C  Layer Stackup:   ')
    assert_equal(str(p), '<IPC-D-356 Parameter: VER=IPC-D-356A>')


def test_eof():
    e = IPC356_EndOfFile()
    assert_equal(e.to_netlist(), '999')
    assert_equal(str(e), '<IPC-D-356 EOF>')


def test_outline():
    type = 'BOARD_EDGE'
    points = [(0.01, 0.01), (2., 2.), (4., 2.), (4., 6.)]
    b = IPC356_Outline(type, points)
    assert_equal(b.type, type)
    assert_equal(b.points, points)
    b = IPC356_Outline.from_line('389BOARD_EDGE         X100Y100 X20000Y20000 X40000 Y60000',
                                 FileSettings(units='inch'))
    assert_equal(b.type, 'BOARD_EDGE')
    assert_equal(b.points, points)


def test_test_record():
    assert_raises(ValueError, IPC356_TestRecord.from_line,
                  'P  JOB', FileSettings())
    record_string = '317+5VDC            VIA   -     D0150PA00X 006647Y 012900X0000          S3'
    r = IPC356_TestRecord.from_line(record_string, FileSettings(units='inch'))
    assert_equal(r.feature_type, 'through-hole')
    assert_equal(r.net_name, '+5VDC')
    assert_equal(r.id, 'VIA')
    assert_almost_equal(r.hole_diameter, 0.015)
    assert_true(r.plated)
    assert_equal(r.access, 'both')
    assert_almost_equal(r.x_coord, 0.6647)
    assert_almost_equal(r.y_coord, 1.29)
    assert_equal(r.rect_x, 0.)
    assert_equal(r.soldermask_info, 'both')
    r = IPC356_TestRecord.from_line(record_string, FileSettings(units='metric'))
    assert_almost_equal(r.hole_diameter, 0.15)
    assert_almost_equal(r.x_coord, 6.647)
    assert_almost_equal(r.y_coord, 12.9)
    assert_equal(r.rect_x, 0.)
    assert_equal(str(r), '<IPC-D-356 +5VDC Test Record: through-hole>')

    record_string = '327+3.3VDC          R40   -1         PA01X 032100Y 007124X0236Y0315R180 S0'
    r = IPC356_TestRecord.from_line(record_string, FileSettings(units='inch'))
    assert_equal(r.feature_type, 'smt')
    assert_equal(r.net_name, '+3.3VDC')
    assert_equal(r.id, 'R40')
    assert_equal(r.pin, '1')
    assert_true(r.plated)
    assert_equal(r.access, 'top')
    assert_almost_equal(r.x_coord, 3.21)
    assert_almost_equal(r.y_coord, 0.7124)
    assert_almost_equal(r.rect_x, 0.0236)
    assert_almost_equal(r.rect_y, 0.0315)
    assert_equal(r.rect_rotation, 180)
    assert_equal(r.soldermask_info, 'none')
    r = IPC356_TestRecord.from_line(
        record_string, FileSettings(units='metric'))
    assert_almost_equal(r.x_coord, 32.1)
    assert_almost_equal(r.y_coord, 7.124)
    assert_almost_equal(r.rect_x, 0.236)
    assert_almost_equal(r.rect_y, 0.315)

    record_string = '317                 J4    -M2   D0330PA00X 012447Y 008030X0000          S1'
    r = IPC356_TestRecord.from_line(record_string, FileSettings(units='inch'))
    assert_equal(r.feature_type, 'through-hole')
    assert_equal(r.id, 'J4')
    assert_equal(r.pin, 'M2')
    assert_almost_equal(r.hole_diameter, 0.033)
    assert_true(r.plated)
    assert_equal(r.access, 'both')
    assert_almost_equal(r.x_coord, 1.2447)
    assert_almost_equal(r.y_coord, 0.8030)
    assert_almost_equal(r.rect_x, 0.)
    assert_equal(r.soldermask_info, 'primary side')

    record_string = '317SCL              COMMUNICATION-1    D  40PA00X  34000Y  20000X 600Y1200R270 '
    r = IPC356_TestRecord.from_line(record_string, FileSettings(units='inch'))
    assert_equal(r.feature_type, 'through-hole')
    assert_equal(r.net_name, 'SCL')
    assert_equal(r.id, 'COMMUNICATION')
    assert_equal(r.pin, '1')
    assert_almost_equal(r.hole_diameter, 0.004)
    assert_true(r.plated)
    assert_almost_equal(r.x_coord, 3.4)
    assert_almost_equal(r.y_coord, 2.0)
