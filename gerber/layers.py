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

from . import common
from .excellon import ExcellonFile
from .ipc356 import IPCNetlist


Hint = namedtuple('Hint', 'layer ext name regex content')

hints = [
    Hint(layer='top',
         ext=['gtl', 'cmp', 'top', ],
         name=['art01', 'top', 'GTL', 'layer1', 'soldcom', 'comp', 'F.Cu', ],
         regex='',
         content=[]
         ),
    Hint(layer='bottom',
         ext=['gbl', 'sld', 'bot', 'sol', 'bottom', ],
         name=['art02', 'bottom', 'bot', 'GBL', 'layer2', 'soldsold', 'B.Cu', ],
         regex='',
         content=[]
         ),
    Hint(layer='internal',
         ext=['in', 'gt1', 'gt2', 'gt3', 'gt4', 'gt5', 'gt6',
              'g1', 'g2', 'g3', 'g4', 'g5', 'g6', ],
         name=['art', 'internal', 'pgp', 'pwr', 'gnd', 'ground',
               'gp1', 'gp2', 'gp3', 'gp4', 'gt5', 'gp6',
               'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu',
               'group3', 'group4', 'group5', 'group6', 'group7', 'group8', ],
         regex='',
         content=[]
         ),
    Hint(layer='topsilk',
         ext=['gto', 'sst', 'plc', 'ts', 'skt', 'topsilk', ],
         name=['sst01', 'topsilk', 'silk', 'slk', 'sst', 'F.SilkS'],
         regex='',
         content=[]
         ),
    Hint(layer='bottomsilk',
         ext=['gbo', 'ssb', 'pls', 'bs', 'skb', 'bottomsilk', ],
         name=['bsilk', 'ssb', 'botsilk', 'bottomsilk', 'B.SilkS'],
         regex='',
         content=[]
         ),
    Hint(layer='topmask',
         ext=['gts', 'stc', 'tmk', 'smt', 'tr', 'topmask', ],
         name=['sm01', 'cmask', 'tmask', 'mask1', 'maskcom', 'topmask',
               'mst', 'F.Mask', ],
         regex='',
         content=[]
         ),
    Hint(layer='bottommask',
         ext=['gbs', 'sts', 'bmk', 'smb', 'br', 'bottommask', ],
         name=['sm', 'bmask', 'mask2', 'masksold', 'botmask', 'bottommask',
               'msb', 'B.Mask', ],
         regex='',
         content=[]
         ),
    Hint(layer='toppaste',
         ext=['gtp', 'tm', 'toppaste', ],
         name=['sp01', 'toppaste', 'pst', 'F.Paste'],
         regex='',
         content=[]
         ),
    Hint(layer='bottompaste',
         ext=['gbp', 'bm', 'bottompaste', ],
         name=['sp02', 'botpaste', 'bottompaste', 'psb', 'B.Paste', ],
         regex='',
         content=[]
         ),
    Hint(layer='outline',
         ext=['gko', 'outline', ],
         name=['BDR', 'border', 'out', 'outline', 'Edge.Cuts', ],
         regex='',
         content=[]
         ),
    Hint(layer='ipc_netlist',
         ext=['ipc'],
         name=[],
         regex='',
         content=[]
         ),
    Hint(layer='drawing',
         ext=['fab'],
         name=['assembly drawing', 'assembly', 'fabrication',
               'fab drawing', 'fab'],
         regex='',
         content=[]
         ),
]


def layer_signatures(layer_class):
    for hint in hints:
        if hint.layer == layer_class:
            return hint.ext + hint.name
    return []


def load_layer(filename):
    return PCBLayer.from_cam(common.read(filename))


def load_layer_data(data, filename=None):
    return PCBLayer.from_cam(common.loads(data, filename))


def guess_layer_class(filename):
    try:
        layer = guess_layer_class_by_content(filename)
        if layer:
            return layer
    except:
        pass

    try:
        directory, filename = os.path.split(filename)
        name, ext = os.path.splitext(filename.lower())
        for hint in hints:
            if hint.regex:
                if re.findall(hint.regex, filename, re.IGNORECASE):
                    return hint.layer

            patterns = [r'^(\w*[.-])*{}([.-]\w*)?$'.format(x) for x in hint.name]
            if ext[1:] in hint.ext or any(re.findall(p, name, re.IGNORECASE) for p in patterns):
                return hint.layer
    except:
        pass
    return 'unknown'


def guess_layer_class_by_content(filename):
    try:
        file = open(filename, 'r')
        for line in file:
            for hint in hints:
                if len(hint.content) > 0:
                    patterns = [r'^(.*){}(.*)$'.format(x) for x in hint.content]
                    if any(re.findall(p, line, re.IGNORECASE) for p in patterns):
                        return hint.layer
    except:
        pass

    return False


def sort_layers(layers, from_top=True):
    layer_order = ['outline', 'toppaste', 'topsilk', 'topmask', 'top',
                   'internal', 'bottom', 'bottommask', 'bottomsilk',
                   'bottompaste']
    append_after = ['drill', 'drawing']

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
    if not from_top:
        output = list(reversed(output))

    for layer_class in append_after:
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
    def from_cam(cls, camfile):
        filename = camfile.filename
        layer_class = guess_layer_class(filename)
        if isinstance(camfile, ExcellonFile) or (layer_class == 'drill'):
            return DrillLayer.from_cam(camfile)
        elif layer_class == 'internal':
            return InternalLayer.from_cam(camfile)
        if isinstance(camfile, IPCNetlist):
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
    def from_cam(cls, camfile):
        return cls(camfile.filename, camfile)

    def __init__(self, filename=None, cam_source=None, layers=None, **kwargs):
        super(DrillLayer, self).__init__(filename, 'drill', cam_source, **kwargs)
        self.layers = layers if layers is not None else ['top', 'bottom']


class InternalLayer(PCBLayer):

    @classmethod
    def from_cam(cls, camfile):
        filename = camfile.filename
        try:
            order = int(re.search(r'\d+', filename).group())
        except AttributeError:
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
