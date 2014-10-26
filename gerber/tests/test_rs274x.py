#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>
from ..rs274x import read, GerberFile
from tests import *

import os

TOP_COPPER_FILE = os.path.join(os.path.dirname(__file__),
                                'resources/top_copper.GTL')


def test_read():
    top_copper = read(TOP_COPPER_FILE)
    assert(isinstance(top_copper, GerberFile))
