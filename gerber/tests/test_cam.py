#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from ..cam import CamFile, FileSettings
from .tests import *


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


def test_bounds_override_smoketest():
    cf = CamFile()
    cf.bounds


def test_zeros():
    """ Test zero/zero_suppression interaction
    """
    fs = FileSettings()
    assert_equal(fs.zero_suppression, 'trailing')
    assert_equal(fs.zeros, 'leading')

    fs['zero_suppression'] = 'leading'
    assert_equal(fs.zero_suppression, 'leading')
    assert_equal(fs.zeros, 'trailing')

    fs.zero_suppression = 'trailing'
    assert_equal(fs.zero_suppression, 'trailing')
    assert_equal(fs.zeros, 'leading')

    fs['zeros'] = 'trailing'
    assert_equal(fs.zeros, 'trailing')
    assert_equal(fs.zero_suppression, 'leading')

    fs.zeros = 'leading'
    assert_equal(fs.zeros, 'leading')
    assert_equal(fs.zero_suppression, 'trailing')

    fs = FileSettings(zeros='leading')
    assert_equal(fs.zeros, 'leading')
    assert_equal(fs.zero_suppression, 'trailing')

    fs = FileSettings(zero_suppression='leading')
    assert_equal(fs.zeros, 'trailing')
    assert_equal(fs.zero_suppression, 'leading')

    fs = FileSettings(zeros='leading', zero_suppression='trailing')
    assert_equal(fs.zeros, 'leading')
    assert_equal(fs.zero_suppression, 'trailing')

    fs = FileSettings(zeros='trailing', zero_suppression='leading')
    assert_equal(fs.zeros, 'trailing')
    assert_equal(fs.zero_suppression, 'leading')


def test_filesettings_validation():
    """ Test FileSettings constructor argument validation
    """
    # absolute-ish is not a valid notation
    assert_raises(ValueError, FileSettings, 'absolute-ish',
                  'inch', None, (2, 5), None)

    # degrees kelvin isn't a valid unit for a CAM file
    assert_raises(ValueError, FileSettings, 'absolute',
                  'degrees kelvin', None, (2, 5), None)

    assert_raises(ValueError, FileSettings, 'absolute',
                  'inch', 'leading', (2, 5), 'leading')

    # Technnically this should be an error, but Eangle files often do this incorrectly so we
    # allow it
    #assert_raises(ValueError, FileSettings, 'absolute',
    #              'inch', 'following', (2, 5), None)

    assert_raises(ValueError, FileSettings, 'absolute',
                  'inch', None, (2, 5), 'following')
    assert_raises(ValueError, FileSettings, 'absolute',
                  'inch', None, (2, 5, 6), None)


def test_key_validation():
    fs = FileSettings()
    assert_raises(KeyError, fs.__getitem__, 'octopus')
    assert_raises(KeyError, fs.__setitem__, 'octopus', 'do not care')
    assert_raises(ValueError, fs.__setitem__, 'notation', 'absolute-ish')
    assert_raises(ValueError, fs.__setitem__, 'units', 'degrees kelvin')
    assert_raises(ValueError, fs.__setitem__, 'zero_suppression', 'following')
    assert_raises(ValueError, fs.__setitem__, 'zeros', 'following')
    assert_raises(ValueError, fs.__setitem__, 'format', (2, 5, 6))
