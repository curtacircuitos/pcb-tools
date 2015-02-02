#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..common import read
from ..excellon import ExcellonFile
from ..rs274x import GerberFile
from tests import *

import os


NCDRILL_FILE = os.path.join(os.path.dirname(__file__),
                                'resources/ncdrill.DRD')
TOP_COPPER_FILE = os.path.join(os.path.dirname(__file__),
                                'resources/top_copper.GTL')

def test_file_type_detection():
    """ Test file type detection
    """
    ncdrill = read(NCDRILL_FILE)
    top_copper = read(TOP_COPPER_FILE)
    assert_true(isinstance(ncdrill, ExcellonFile))
    assert_true(isinstance(top_copper, GerberFile))

def test_file_type_validation():
    """ Test file format validation
    """
    assert_raises(TypeError, read, 'LICENSE')


