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
from collections import namedtuple

Hint = namedtuple('Hint', 'layer ext name')

hints = [
    Hint(layer='top',
         ext=['gtl', 'cmp', 'top', ],
         name=['art01', 'top', 'GTL', 'layer1', 'soldcom', 'comp', ]
         ),
    Hint(layer='bottom',
         ext=['gbl', 'sld', 'bot', 'sol', ],
         name=['art02', 'bottom', 'bot', 'GBL', 'layer2', 'soldsold', ]
         ),
    Hint(layer='internal',
         ext=['in', 'gt1', 'gt2', 'gt3', 'gt4', 'gt5', 'gt6', 'g1',
              'g2', 'g3', 'g4', 'g5', 'g6', ],
         name=['art', 'internal']
         ),
    # TODO how does this have to be handled?
    # Hint(layer='power_plane',
    #      ext=None,
    #      name=['pgp', 'pwr', ],
    #      ),
    # Hint(layer='ground_plane',
    #      ext=None,
    #      name=['gp1', 'gp2', 'gp3', 'gp4', 'gt5', 'gp6', 'gnd',
    #            'ground', ]
    #      ),
    Hint(layer='topsilk',
         ext=['gto', 'sst', 'plc', 'ts', 'skt', ],
         name=['sst01', 'topsilk', 'silk', 'slk', 'sst', ]
         ),
    Hint(layer='bottomsilk',
         ext=['gbo', 'ssb', 'pls', 'bs', 'skb', ],
         name=['sst', 'bsilk', 'ssb', 'botsilk', ]
         ),
    Hint(layer='topmask',
         ext=['gts', 'stc', 'tmk', 'smt', 'tr', ],
         name=['sm01', 'cmask', 'tmask', 'mask1', 'maskcom', 'topmask',
               'mst', ]
         ),
    Hint(layer='bottommask',
         ext=['gbs', 'sts', 'bmk', 'smb', 'br', ],
         name=['sm', 'bmask', 'mask2', 'masksold', 'botmask', 'msb', ]
         ),
    Hint(layer='toppaste',
         ext=['gtp', 'tm'],
         name=['sp01', 'toppaste', 'pst']
         ),
    Hint(layer='bottompaste',
         ext=['gbp', 'bm'],
         name=['sp02', 'botpaste', 'psb']
         ),
    Hint(layer='outline',
         ext=['gko'],
         name=['BDR', 'border', 'out', ]
         ),
]


class GerberLayerDialect(object):
    def __init__(self, filenames):
        self._filenames = filenames
        self._outline = None
        self._top = None
        self._topsilk = None
        self._topmask = None
        self._toppaste = None
        self._bottom = None
        self._bottomsilk = None
        self._bottommask = None
        self._bottompaste = None
        self._internal = None
        self._drill = None
        self._fab = None
        self._unknown = None
        self._guess_layers()

    def guess_layer(self, filename):
        raise NotImplementedError

    def _guess_layers(self):
        self._internal = []
        self._unknown = []

        for filename in self._filenames:
            layer = self.guess_layer(filename)
            if layer == 'internal':
                self._internal.append(filename)
            elif layer == 'unknown':
                self._unknown.append(filename)
            else:
                self.__setattr__('_' + layer, filename)

    @property
    def outline(self):
        return self._outline

    @property
    def top(self):
        return self._top

    @property
    def topsilk(self):
        return self._topsilk

    @property
    def toppaste(self):
        return self._toppaste

    @property
    def topmask(self):
        return self._topmask

    @property
    def bottom(self):
        return self._bottom

    @property
    def bottomsilk(self):
        return self._bottomsilk

    @property
    def bottompaste(self):
        return self._bottompaste

    @property
    def bottommask(self):
        return self._bottommask

    @property
    def internal(self):
        return self._internal

    @property
    def drill(self):
        return self._drill

    @property
    def fab(self):
        return self._fab

    @property
    def unknown(self):
        return self._unknown

    @property
    def silk_layers(self):
        return [self.topsilk, self.bottomsilk]

    @property
    def mask_layers(self):
        return [self.topmask, self.bottommask]

    @property
    def paste_layers(self):
        return [self.toppaste, self.bottompaste]

    @property
    def outer_copper_layers(self):
        return [self.top, self.bottom]

    @property
    def top_layers(self):
        return [self.top, self.topmask,
                self.topsilk, self.toppaste]

    @property
    def bottom_layers(self):
        return [self.bottom, self.bottompaste,
                self.bottomsilk, self.bottompaste]

    @property
    def top_assembly(self):
        return self.top_layers + [self.outline]

    @property
    def bottom_assembly(self):
        return self.bottom_layers + [self.outline]

    def print_layermap(self):
        print('TOP         {0}'.format(self.top))
        print('TOPSILK     {0}'.format(self.topsilk))
        print('TOPMASK     {0}'.format(self.topmask))
        print('TOPPASTE    {0}'.format(self.toppaste))
        print('BOTTOM      {0}'.format(self.bottom))
        print('BOTTOMSILK  {0}'.format(self.bottomsilk))
        print('BOTTOMMASK  {0}'.format(self.bottommask))
        print('BOTTOMPASTE {0}'.format(self.bottompaste))
        print('OUTLINE     {0}'.format(self.outline))
        print('INTERNAL : ')
        if self._internal:
            for filename in self._internal:
                print('            {0}'.format(filename))
        else:
            print('            None')
        print('UNKNOWN : ')
        if self._unknown:
            for filename in self._unknown:
                print('            {0}'.format(filename))
        else:
            print('            None')


class GenericLayerDialect(GerberLayerDialect):
    def guess_layer(self, filename):
        directory, name = os.path.split(filename)
        name, ext = os.path.splitext(name)
        for hint in hints:
            if ext in hint.ext or \
                    any(x in name for x in hint.name):
                return hint.layer


class GedaGerberLayerDialect(GerberLayerDialect):
    def guess_layer(self, filename):
        directory, name = os.path.split(filename)
        name, ext = os.path.splitext(name)
        if ext == '.gbr':
            if name.endswith('.top'):
                return 'top'
            elif name.endswith('.topmask'):
                return 'topmask'
            elif name.endswith('.toppaste'):
                return 'toppaste'
            elif name.endswith('.topsilk'):
                return 'topsilk'
            elif name.endswith('.bottom'):
                return 'bottom'
            elif name.endswith('.bottommask'):
                return 'bottommask'
            elif name.endswith('.bottompaste'):
                return 'bottompaste'
            elif name.endswith('.bottomsilk'):
                return 'bottomsilk'
            elif name.endswith('.fab'):
                return 'fab'
            elif name.endswith('.outline'):
                return 'outline'
            else:
                return 'unknown'
        if ext == '.cnc':
            return 'drill'


available_dialects = {
    'generic': GenericLayerDialect,
    'geda': GedaGerberLayerDialect
}


def guess_dialect(filenames, verbose=False):
    if verbose:
        print("Attempting to guess layer name dialect.")
    for key, dialect in available_dialects.iteritems():
        if verbose:
            print("Trying {0}".format(key))
        result = dialect(filenames)
        if not result.unknown:
            print("All files recognized. Using dialect {0}".format(key))
            return dialect
        else:
            print("Unrecognized files with dialect {0} : ".format(key))
            for filename in result.unknown:
                print(filename)
