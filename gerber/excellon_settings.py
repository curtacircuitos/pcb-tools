#!/usr/bin/env python
# -*- coding: utf-8 -*-
from argparse import PARSER

# Copyright 2015 Garret Fick <garret@ficksworkshop.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Excellon Settings Definition File module
====================
**Excellon file classes**

This module provides Excellon file classes and parsing utilities
"""

import re
try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO
    
from .cam import FileSettings
    
def loads(data):
    """ Read settings file information and return an FileSettings
    Parameters
    ----------
    data : string
        string containing Excellon settings file contents

    Returns
    -------
    file settings: FileSettings

    """
    
    return ExcellonSettingsParser().parse_raw(data)

def map_coordinates(value):
    if value == 'ABSOLUTE':
        return 'absolute'
    return 'relative'

def map_units(value):
    if value == 'ENGLISH':
        return 'inch'
    return 'metric'

def map_boolean(value):
    return value == 'YES'

SETTINGS_KEYS = {
              'INTEGER-PLACES': (int, 'format-int'),
              'DECIMAL-PLACES': (int, 'format-dec'),
              'COORDINATES': (map_coordinates, 'notation'),
              'OUTPUT-UNITS': (map_units, 'units'),
              }

class ExcellonSettingsParser(object):
    """Excellon Settings PARSER
    
    Parameters
    ----------
    None
    """
    
    def __init__(self):
        self.values = {}
        self.settings = None
    
    def parse_raw(self, data):
        for line in StringIO(data):
            self._parse(line.strip())
            
        # Create the FileSettings object
        self.settings = FileSettings(
                                     notation=self.values['notation'],
                                     units=self.values['units'],
                                     format=(self.values['format-int'], self.values['format-dec'])
                                     )
        
        return self.settings
            
    def _parse(self, line):
        
        line_items = line.split()
        if len(line_items) == 2:
            
            item_type_info = SETTINGS_KEYS.get(line_items[0])
            if item_type_info:
                # Convert the value to the expected type
                item_value = item_type_info[0](line_items[1])
                
                self.values[item_type_info[1]] = item_value