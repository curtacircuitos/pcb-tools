#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Chintalagiri Shashank <shashank@chintal.in>

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
Docstring for freecad_backend
"""

from .render import GerberContext
from .render import PCBContext

from operator import mul
import math
import tempfile
import os

from ..primitives import *


class GerberFreecadContext(GerberContext):
    pass


class PCBFreecadContext(PCBContext):
    def render(self, output_filename=None):
        if self.dialect:
            layers = self.dialect(self.filenames)
            if self.verbose:
                print("Using Layers : ")
                layers.print_layermap()
        else:
            raise AttributeError('FreeCAD backend needs a valid layer map to do '
                                 'anything. Specify an implemented layer name '
                                 'dialect and try again. ')
        if os.path.splitext(output_filename)[1].upper() != 'FCSTD':
            output_filename += '.fcstd'
