#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from ..cnc import CncFile, FileSettings
from tests import *


def test_smoke_filesettings():
    """ Smoke test FileSettings class
    """
    fs = FileSettings()


def test_filesettings_defaults():
    """ Test FileSettings default values
    """
    fs = FileSettings()
    assert_equal(fs.format, (2, 5))
    assert_equal(fs.notation, 'absolute')
    assert_equal(fs.zero_suppression, 'trailing')
    assert_equal(fs.units, 'inch')


def test_filesettings_dict():
    """ Test FileSettings Dict
    """
    fs = FileSettings()
    assert_equal(fs['format'], (2, 5))
    assert_equal(fs['notation'], 'absolute')
    assert_equal(fs['zero_suppression'], 'trailing')
    assert_equal(fs['units'], 'inch')


def test_filesettings_assign():
    """ Test FileSettings attribute assignment
    """
    fs = FileSettings()
    fs.units = 'test'
    fs.notation = 'test'
    fs.zero_suppression = 'test'
    fs.format = 'test'
    assert_equal(fs.units, 'test')
    assert_equal(fs.notation, 'test')
    assert_equal(fs.zero_suppression, 'test')
    assert_equal(fs.format, 'test')

    def test_smoke_cncfile():
        pass
