#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
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
import re
from collections import namedtuple

from .excellon import ExcellonFile
from .ipc356 import IPC_D_356


Hint = namedtuple('Hint', 'layer ext name')

hints = [
    Hint(layer='top',
         ext=['gtl', 'cmp', 'top', ],
         name=['art01', 'top', 'GTL', 'layer1', 'soldcom', 'comp', ]
         ),
    Hint(layer='bottom',
         ext=['gbl', 'sld', 'bot', 'sol', 'bottom', ],
         name=['art02', 'bottom', 'bot', 'GBL', 'layer2', 'soldsold', ]
         ),
    Hint(layer='internal',
         ext=['in', 'gt1', 'gt2', 'gt3', 'gt4', 'gt5', 'gt6', 'g1',
              'g2', 'g3', 'g4', 'g5', 'g6', ],
         name=['art', 'internal', 'pgp', 'pwr', 'gp1', 'gp2', 'gp3', 'gp4',
               'gt5', 'gp6', 'gnd', 'ground', ]
         ),
    Hint(layer='topsilk',
         ext=['gto', 'sst', 'plc', 'ts', 'skt', 'topsilk', ],
         name=['sst01', 'topsilk', 'silk', 'slk', 'sst', ]
         ),
    Hint(layer='bottomsilk',
         ext=['gbo', 'ssb', 'pls', 'bs', 'skb', 'bottomsilk', ],
         name=['bsilk', 'ssb', 'botsilk', ]
         ),
    Hint(layer='topmask',
         ext=['gts', 'stc', 'tmk', 'smt', 'tr', 'topmask', ],
         name=['sm01', 'cmask', 'tmask', 'mask1', 'maskcom', 'topmask',
               'mst', ]
         ),
    Hint(layer='bottommask',
         ext=['gbs', 'sts', 'bmk', 'smb', 'br', 'bottommask', ],
         name=['sm', 'bmask', 'mask2', 'masksold', 'botmask', 'msb', ]
         ),
    Hint(layer='toppaste',
         ext=['gtp', 'tm', 'toppaste', ],
         name=['sp01', 'toppaste', 'pst']
         ),
    Hint(layer='bottompaste',
         ext=['gbp', 'bm', 'bottompaste', ],
         name=['sp02', 'botpaste', 'psb']
         ),
    Hint(layer='outline',
         ext=['gko', 'outline', ],
         name=['BDR', 'border', 'out', ]
         ),
    Hint(layer='ipc_netlist',
         ext=['ipc'],
         name=[],
         ),
]


def guess_layer_class(filename):
    try:
        directory, name = os.path.split(filename)
        name, ext = os.path.splitext(name.lower())
        for hint in hints:
            patterns = [r'^(\w*[.-])*{}([.-]\w*)?$'.format(x) for x in hint.name]
            if ext[1:] in hint.ext or any(re.findall(p, name, re.IGNORECASE) for p in patterns):
                return hint.layer
    except:
        pass
    return 'unknown'


def sort_layers(layers):
    layer_order = ['outline', 'toppaste', 'topsilk', 'topmask', 'top',
                   'internal', 'bottom', 'bottommask', 'bottomsilk',
                   'bottompaste', 'drill', ]
    output = []
    drill_layers = [layer for layer in layers if layer.layer_class == 'drill']
    internal_layers = list(sorted([layer for layer in layers
                                   if layer.layer_class == 'internal']))

    for layer_class in layer_order:
        if layer_class == 'internal':
            output += internal_layers
        elif layer_class == 'drill':
            output += drill_layers
        else:
            for layer in layers:
                if layer.layer_class == layer_class:
                    output.append(layer)
    return output


class PCBLayer(object):
    """ Base class for PCB Layers

    Parameters
    ----------
    source : CAMFile
        CAMFile representing the layer


    Attributes
    ----------
    filename : string
        Source Filename

    """
    @classmethod
    def from_gerber(cls, camfile):
        filename = camfile.filename
        layer_class = guess_layer_class(filename)
        if isinstance(camfile, ExcellonFile) or (layer_class == 'drill'):
            return DrillLayer.from_gerber(camfile)
        elif layer_class == 'internal':
            return InternalLayer.from_gerber(camfile)
        if isinstance(camfile, IPC_D_356):
            layer_class = 'ipc_netlist'
        return cls(filename, layer_class, camfile)

    def __init__(self, filename=None, layer_class=None, cam_source=None, **kwargs):
        super(PCBLayer, self).__init__(**kwargs)
        self.filename = filename
        self.layer_class = layer_class
        self.cam_source = cam_source
        self.surface = None
        self.primitives = cam_source.primitives if cam_source is not None else []

    @property
    def bounds(self):
        if self.cam_source is not None:
            return self.cam_source.bounds
        else:
            return None

    def __repr__(self):
        return '<PCBLayer: {}>'.format(self.layer_class)

class DrillLayer(PCBLayer):
    @classmethod
    def from_gerber(cls, camfile):
        return cls(camfile.filename, camfile)

    def __init__(self, filename=None, cam_source=None, layers=None, **kwargs):
        super(DrillLayer, self).__init__(filename, 'drill', cam_source, **kwargs)
        self.layers = layers if layers is not None else ['top', 'bottom']


class InternalLayer(PCBLayer):

    @classmethod
    def from_gerber(cls, camfile):
        filename = camfile.filename
        try:
            order = int(re.search(r'\d+', filename).group())
        except:
            order = 0
        return cls(filename, camfile, order)

    def __init__(self, filename=None, cam_source=None, order=0, **kwargs):
        super(InternalLayer, self).__init__(filename, 'internal', cam_source, **kwargs)
        self.order = order

    def __eq__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order == other.order)

    def __ne__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order != other.order)

    def __gt__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order > other.order)

    def __lt__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order < other.order)

    def __ge__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order >= other.order)

    def __le__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order <= other.order)


class LayerSet(object):

    def __init__(self, name, layers, **kwargs):
        super(LayerSet, self).__init__(**kwargs)
        self.name = name
        self.layers = list(layers)

    def __len__(self):
        return len(self.layers)

    def __getitem__(self, item):
        return self.layers[item]

    def to_render(self):
        return self.layers

    def apply_theme(self, theme):
        pass
