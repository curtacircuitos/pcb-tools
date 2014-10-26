#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..excellon import read, detect_excellon_format, ExcellonFile
from tests import *

import os

NCDRILL_FILE = os.path.join(os.path.dirname(__file__),
                                'resources/ncdrill.DRD')

def test_format_detection():
    """ Test file type detection
    """
    settings = detect_excellon_format(NCDRILL_FILE)
    assert_equal(settings['format'], (2, 4))
    assert_equal(settings['zero_suppression'], 'leading')

def test_read():
    ncdrill = read(NCDRILL_FILE)
    assert(isinstance(ncdrill, ExcellonFile))
    
def test_read_settings():
    ncdrill = read(NCDRILL_FILE)
    assert_equal(ncdrill.settings.format, (2, 4))
    assert_equal(ncdrill.settings.zero_suppression, 'leading')
    
    
    
    
    
