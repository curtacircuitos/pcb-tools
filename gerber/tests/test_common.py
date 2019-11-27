#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..exceptions import ParseError
from ..common import read, loads
from ..excellon import ExcellonFile
from ..rs274x import GerberFile
import os
import pytest


NCDRILL_FILE = os.path.join(os.path.dirname(__file__), "resources/ncdrill.DRD")
TOP_COPPER_FILE = os.path.join(os.path.dirname(__file__), "resources/top_copper.GTL")


def test_file_type_detection():
    """ Test file type detection
    """
    ncdrill = read(NCDRILL_FILE)
    top_copper = read(TOP_COPPER_FILE)
    assert isinstance(ncdrill, ExcellonFile)
    assert isinstance(top_copper, GerberFile)


def test_load_from_string():
    with open(NCDRILL_FILE, "rU") as f:
        ncdrill = loads(f.read())
    with open(TOP_COPPER_FILE, "rU") as f:
        top_copper = loads(f.read())
    assert isinstance(ncdrill, ExcellonFile)
    assert isinstance(top_copper, GerberFile)


def test_file_type_validation():
    """ Test file format validation
    """
    pytest.raises(ParseError, read, __file__)
