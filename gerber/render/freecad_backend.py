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

import os
import platform
import sys

from .render import GerberContext
from .render import PCBContext

try:
    import FreeCAD
    import FreeCADGui
except ImportError:
    if 'FREECADPATH' in os.environ.keys():
        FREECADPATH = os.environ['FREECADPATH']
    else:
        if platform.system() == 'Windows':
            FREECADPATH = '/c/apps/FreeCAD/bin'
        else:
            FREECADPATH = '/usr/lib/freecad/lib'
    sys.path.append(FREECADPATH)
    import FreeCAD
    import FreeCADGui


class GerberFreecadContext(GerberContext):
    pass


class PCBFreecadContext(PCBContext):
    def __init__(self, filenames, dialect, verbose):
        super(PCBFreecadContext, self).__init__(filenames, dialect, verbose)
        self._output_name = None
        self._output_file = None

    def _create_output_file(self):
        try:
            os.remove(self._output_name + '.fcstd')
        except OSError:
            pass
        self._output_file = FreeCAD.newDocument(self._output_name)

    def _write_output_file(self):
        self._output_file.saveAs(self._output_name + '.fcstd')

    def _create_body(self):
        pass

    def _create_top_surface(self):
        self._create_top_copper()
        self._create_top_mask()
        self._create_top_silk()
        self._create_top_paste()

    def _create_top_copper(self):
        pass

    def _create_top_mask(self):
        pass

    def _create_top_silk(self):
        pass

    def _create_top_paste(self):
        pass

    def _create_bottom_surface(self):
        self._create_bottom_copper()
        self._create_bottom_mask()
        self._create_bottom_silk()
        self._create_bottom_paste()

    def _create_bottom_copper(self):
        pass

    def _create_bottom_mask(self):
        pass

    def _create_bottom_silk(self):
        pass

    def _create_bottom_paste(self):
        pass

    def render(self, output_filename=None):
        if self.dialect:
            self.layers = self.dialect(self.filenames)
            if self.verbose:
                print("Using Layers : ")
                self.layers.print_layermap()
        else:
            raise AttributeError('FreeCAD backend needs a valid layer map to do '
                                 'anything. Specify an implemented layer name '
                                 'dialect and try again. ')
        if not output_filename:
            output_filename = self.layers.pcbname
        if os.path.splitext(output_filename)[1].upper() == 'FCSTD':
            output_filename = output_filename[:-len('.fcstd')]
        self._output_name = output_filename

        self._create_output_file()

        self._create_body()
        self._create_top_surface()
        self._create_bottom_surface()

        self._write_output_file()
