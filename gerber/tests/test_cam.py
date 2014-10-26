#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from ..cam import CamFile, FileSettings
from tests import *


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
    fs.units = 'test1'
    fs.notation = 'test2'
    fs.zero_suppression = 'test3'
    fs.format = 'test4'
    assert_equal(fs.units, 'test1')
    assert_equal(fs.notation, 'test2')
    assert_equal(fs.zero_suppression, 'test3')
    assert_equal(fs.format, 'test4')


def test_filesettings_dict_assign():
    """ Test FileSettings dict-style attribute assignment
    """
    fs = FileSettings()
    fs['units'] = 'metric'
    fs['notation'] = 'incremental'
    fs['zero_suppression'] = 'leading'
    fs['format'] = (1, 2)
    assert_equal(fs.units, 'metric')
    assert_equal(fs.notation, 'incremental')
    assert_equal(fs.zero_suppression, 'leading')
    assert_equal(fs.format, (1, 2))

def test_camfile_init():
    """ Smoke test CamFile test
    """
    cf = CamFile()

def test_camfile_settings():
    """ Test CamFile Default Settings
    """
    cf = CamFile()
    assert_equal(cf.settings, FileSettings())
    
    