#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

import pytest

from ..cam import CamFile, FileSettings


def test_filesettings_defaults():
    """ Test FileSettings default values
    """
    fs = FileSettings()
    assert fs.format == (2, 5)
    assert fs.notation == "absolute"
    assert fs.zero_suppression == "trailing"
    assert fs.units == "inch"


def test_filesettings_dict():
    """ Test FileSettings Dict
    """
    fs = FileSettings()
    assert fs["format"] == (2, 5)
    assert fs["notation"] == "absolute"
    assert fs["zero_suppression"] == "trailing"
    assert fs["units"] == "inch"


def test_filesettings_assign():
    """ Test FileSettings attribute assignment
    """
    fs = FileSettings()
    fs.units = "test1"
    fs.notation = "test2"
    fs.zero_suppression = "test3"
    fs.format = "test4"
    assert fs.units == "test1"
    assert fs.notation == "test2"
    assert fs.zero_suppression == "test3"
    assert fs.format == "test4"


def test_filesettings_dict_assign():
    """ Test FileSettings dict-style attribute assignment
    """
    fs = FileSettings()
    fs["units"] = "metric"
    fs["notation"] = "incremental"
    fs["zero_suppression"] = "leading"
    fs["format"] = (1, 2)
    assert fs.units == "metric"
    assert fs.notation == "incremental"
    assert fs.zero_suppression == "leading"
    assert fs.format == (1, 2)


def test_camfile_init():
    """ Smoke test CamFile test
    """
    cf = CamFile()


def test_camfile_settings():
    """ Test CamFile Default Settings
    """
    cf = CamFile()
    assert cf.settings == FileSettings()


def test_bounds_override_smoketest():
    cf = CamFile()
    cf.bounds


def test_zeros():
    """ Test zero/zero_suppression interaction
    """
    fs = FileSettings()
    assert fs.zero_suppression == "trailing"
    assert fs.zeros == "leading"

    fs["zero_suppression"] = "leading"
    assert fs.zero_suppression == "leading"
    assert fs.zeros == "trailing"

    fs.zero_suppression = "trailing"
    assert fs.zero_suppression == "trailing"
    assert fs.zeros == "leading"

    fs["zeros"] = "trailing"
    assert fs.zeros == "trailing"
    assert fs.zero_suppression == "leading"

    fs.zeros = "leading"
    assert fs.zeros == "leading"
    assert fs.zero_suppression == "trailing"

    fs = FileSettings(zeros="leading")
    assert fs.zeros == "leading"
    assert fs.zero_suppression == "trailing"

    fs = FileSettings(zero_suppression="leading")
    assert fs.zeros == "trailing"
    assert fs.zero_suppression == "leading"

    fs = FileSettings(zeros="leading", zero_suppression="trailing")
    assert fs.zeros == "leading"
    assert fs.zero_suppression == "trailing"

    fs = FileSettings(zeros="trailing", zero_suppression="leading")
    assert fs.zeros == "trailing"
    assert fs.zero_suppression == "leading"


def test_filesettings_validation():
    """ Test FileSettings constructor argument validation
    """
    # absolute-ish is not a valid notation
    pytest.raises(ValueError, FileSettings, "absolute-ish", "inch", None, (2, 5), None)

    # degrees kelvin isn't a valid unit for a CAM file
    pytest.raises(
        ValueError, FileSettings, "absolute", "degrees kelvin", None, (2, 5), None
    )

    pytest.raises(
        ValueError, FileSettings, "absolute", "inch", "leading", (2, 5), "leading"
    )

    # Technnically this should be an error, but Eangle files often do this incorrectly so we
    # allow it
    # pytest.raises(ValueError, FileSettings, 'absolute',
    #              'inch', 'following', (2, 5), None)

    pytest.raises(
        ValueError, FileSettings, "absolute", "inch", None, (2, 5), "following"
    )
    pytest.raises(ValueError, FileSettings, "absolute", "inch", None, (2, 5, 6), None)


def test_key_validation():
    fs = FileSettings()
    pytest.raises(KeyError, fs.__getitem__, "octopus")
    pytest.raises(KeyError, fs.__setitem__, "octopus", "do not care")
    pytest.raises(ValueError, fs.__setitem__, "notation", "absolute-ish")
    pytest.raises(ValueError, fs.__setitem__, "units", "degrees kelvin")
    pytest.raises(ValueError, fs.__setitem__, "zero_suppression", "following")
    pytest.raises(ValueError, fs.__setitem__, "zeros", "following")
    pytest.raises(ValueError, fs.__setitem__, "format", (2, 5, 6))
