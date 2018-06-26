#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2016 Hamilton Kibbe <ham@hamiltonkib.be>
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

from .tests import *
from ..layers import *
from ..common import read

NCDRILL_FILE = os.path.join(os.path.dirname(__file__),
                            'resources/ncdrill.DRD')
NETLIST_FILE = os.path.join(os.path.dirname(__file__),
                            'resources/ipc-d-356.ipc')
COPPER_FILE = os.path.join(os.path.dirname(__file__),
                           'resources/top_copper.GTL')

def test_guess_layer_class():
    """ Test layer type inferred correctly from filename
    """

    # Add any specific test cases here (filename, layer_class)
    test_vectors = [(None, 'unknown'), ('NCDRILL.TXT', 'unknown'),
                    ('example_board.gtl', 'top'),
                    ('exampmle_board.sst', 'topsilk'),
                    ('ipc-d-356.ipc', 'ipc_netlist'), ]

    for hint in hints:
        for ext in hint.ext:
            assert_equal(hint.layer, guess_layer_class('board.{}'.format(ext)))
        for name in hint.name:
            assert_equal(hint.layer, guess_layer_class('{}.pho'.format(name)))

    for filename, layer_class in test_vectors:
        assert_equal(layer_class, guess_layer_class(filename))

def test_guess_layer_class_regex():
    """ Test regular expressions for layer matching
    """

    # Add any specific test case (filename, layer_class)
    test_vectors = [('test - top copper.gbr', 'top'),
                    ('test - copper top.gbr', 'top'), ]

    # Add custom regular expressions
    layer_hints = [
        Hint(layer='top',
                ext=[],
                name=[],
                regex=r'(.*)(\scopper top\.gbr|\stop copper\.gbr)'
            ),
    ]
    hints.extend(layer_hints)

    for filename, layer_class in test_vectors:
        assert_equal(layer_class, guess_layer_class(filename))


def test_sort_layers():
    """ Test layer ordering
    """
    layers = [
        PCBLayer(layer_class='drawing'),
        PCBLayer(layer_class='drill'),
        PCBLayer(layer_class='bottompaste'),
        PCBLayer(layer_class='bottomsilk'),
        PCBLayer(layer_class='bottommask'),
        PCBLayer(layer_class='bottom'),
        PCBLayer(layer_class='internal'),
        PCBLayer(layer_class='top'),
        PCBLayer(layer_class='topmask'),
        PCBLayer(layer_class='topsilk'),
        PCBLayer(layer_class='toppaste'),
        PCBLayer(layer_class='outline'),
    ]

    layer_order = ['outline', 'toppaste', 'topsilk', 'topmask', 'top',
                   'internal', 'bottom', 'bottommask', 'bottomsilk',
                   'bottompaste', 'drill', 'drawing']
    bottom_order = list(reversed(layer_order[:10])) + layer_order[10:]
    assert_equal([l.layer_class for l in sort_layers(layers)], layer_order)
    assert_equal([l.layer_class for l in sort_layers(layers, from_top=False)],
                 bottom_order)


def test_PCBLayer_from_file():
    layer = PCBLayer.from_cam(read(COPPER_FILE))
    assert_true(isinstance(layer, PCBLayer))
    layer = PCBLayer.from_cam(read(NCDRILL_FILE))
    assert_true(isinstance(layer, DrillLayer))
    layer = PCBLayer.from_cam(read(NETLIST_FILE))
    assert_true(isinstance(layer, PCBLayer))
    assert_equal(layer.layer_class, 'ipc_netlist')


def test_PCBLayer_bounds():
    source = read(COPPER_FILE)
    layer = PCBLayer.from_cam(source)
    assert_equal(source.bounds, layer.bounds)


def test_DrillLayer_from_cam():
    no_exceptions = True
    try:
        layer = DrillLayer.from_cam(read(NCDRILL_FILE))
        assert_true(isinstance(layer, DrillLayer))
    except:
        no_exceptions = False
    assert_true(no_exceptions)
