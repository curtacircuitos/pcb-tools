#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2015 Hamilton Kibbe <ham@hamiltonkib.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from .exceptions import ParseError
from .layers import PCBLayer, sort_layers
from .common import read as gerber_read
from .utils import listdir


class PCB(object):

    @classmethod
    def from_directory(cls, directory, board_name=None, verbose=False):
        layers = []
        names = set()

        # Validate
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise TypeError('{} is not a directory.'.format(directory))

        # Load gerber files
        for filename in listdir(directory, True, True):
            try:
                camfile = gerber_read(os.path.join(directory, filename))
                layer = PCBLayer.from_cam(camfile)
                layers.append(layer)
                names.add(os.path.splitext(filename)[0])
                if verbose:
                    print('[PCB]: Added {} layer <{}>'.format(layer.layer_class,
                                                              filename))
            except ParseError:
                if verbose:
                    print('[PCB]: Skipping file {}'.format(filename))
            except IOError:
                if verbose:
                    print('[PCB]: Skipping file {}'.format(filename))

        # Try to guess board name
        if board_name is None:
            if len(names) == 1:
                board_name = names.pop()
            else:
                board_name = os.path.basename(directory)
        # Return PCB
        return cls(layers, board_name)

    def __init__(self, layers, name=None):
        self.layers = sort_layers(layers)
        self.name = name

    def __len__(self):
        return len(self.layers)

    @property
    def top_layers(self):
        board_layers = [l for l in reversed(self.layers) if l.layer_class in
                        ('topsilk', 'topmask', 'top')]
        drill_layers = [l for l in self.drill_layers if 'top' in l.layers]
        # Drill layer goes under soldermask for proper rendering of tented vias
        return [board_layers[0]] + drill_layers + board_layers[1:]

    @property
    def bottom_layers(self):
        board_layers = [l for l in self.layers if l.layer_class in
                        ('bottomsilk', 'bottommask', 'bottom')]
        drill_layers = [l for l in self.drill_layers if 'bottom' in l.layers]
        # Drill layer goes under soldermask for proper rendering of tented vias
        return [board_layers[0]] + drill_layers + board_layers[1:]

    @property
    def drill_layers(self):
        return [l for l in self.layers if l.layer_class == 'drill']

    @property
    def copper_layers(self):
        return list(reversed([layer for layer in self.layers if
                              layer.layer_class in
                              ('top', 'bottom', 'internal')]))

    @property
    def layer_count(self):
        """ Number of *COPPER* layers
        """
        return len([l for l in self.layers if l.layer_class in
                    ('top', 'bottom', 'internal')])

    @property
    def board_bounds(self):
        for layer in self.layers:
            if layer.layer_class == 'outline':
                return layer.bounds
        for layer in self.layers:
            if layer.layer_class == 'top':
                return layer.bounds
