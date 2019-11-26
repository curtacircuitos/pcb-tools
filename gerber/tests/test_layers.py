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

from ..layers import *
from ..common import read

NCDRILL_FILE = os.path.join(os.path.dirname(__file__), "resources/ncdrill.DRD")
NETLIST_FILE = os.path.join(os.path.dirname(__file__), "resources/ipc-d-356.ipc")
COPPER_FILE = os.path.join(os.path.dirname(__file__), "resources/top_copper.GTL")


def test_guess_layer_class():
    """ Test layer type inferred correctly from filename
    """

    # Add any specific test cases here (filename, layer_class)
    test_vectors = [
        (None, "unknown"),
        ("NCDRILL.TXT", "unknown"),
        ("example_board.gtl", "top"),
        ("exampmle_board.sst", "topsilk"),
        ("ipc-d-356.ipc", "ipc_netlist"),
    ]

    for hint in hints:
        for ext in hint.ext:
            assert hint.layer == guess_layer_class("board.{}".format(ext))
        for name in hint.name:
            assert hint.layer == guess_layer_class("{}.pho".format(name))

    for filename, layer_class in test_vectors:
        assert layer_class == guess_layer_class(filename)


def test_guess_layer_class_regex():
    """ Test regular expressions for layer matching
    """

    # Add any specific test case (filename, layer_class)
    test_vectors = [("test - top copper.gbr", "top"), ("test - copper top.gbr", "top")]

    # Add custom regular expressions
    layer_hints = [
        Hint(
            layer="top",
            ext=[],
            name=[],
            regex=r"(.*)(\scopper top|\stop copper).gbr",
            content=[],
        )
    ]
    hints.extend(layer_hints)

    for filename, layer_class in test_vectors:
        assert layer_class == guess_layer_class(filename)


def test_guess_layer_class_by_content():
    """ Test layer class by checking content
    """

    expected_layer_class = "bottom"
    filename = os.path.join(
        os.path.dirname(__file__), "resources/example_guess_by_content.g0"
    )

    layer_hints = [
        Hint(
            layer="bottom",
            ext=[],
            name=[],
            regex="",
            content=["G04 Layer name: Bottom"],
        )
    ]
    hints.extend(layer_hints)

    assert expected_layer_class == guess_layer_class_by_content(filename)


def test_sort_layers():
    """ Test layer ordering
    """
    layers = [
        PCBLayer(layer_class="drawing"),
        PCBLayer(layer_class="drill"),
        PCBLayer(layer_class="bottompaste"),
        PCBLayer(layer_class="bottomsilk"),
        PCBLayer(layer_class="bottommask"),
        PCBLayer(layer_class="bottom"),
        PCBLayer(layer_class="internal"),
        PCBLayer(layer_class="top"),
        PCBLayer(layer_class="topmask"),
        PCBLayer(layer_class="topsilk"),
        PCBLayer(layer_class="toppaste"),
        PCBLayer(layer_class="outline"),
    ]

    layer_order = [
        "outline",
        "toppaste",
        "topsilk",
        "topmask",
        "top",
        "internal",
        "bottom",
        "bottommask",
        "bottomsilk",
        "bottompaste",
        "drill",
        "drawing",
    ]
    bottom_order = list(reversed(layer_order[:10])) + layer_order[10:]
    assert [l.layer_class for l in sort_layers(layers)] == layer_order
    assert [l.layer_class for l in sort_layers(layers, from_top=False)] == bottom_order


def test_PCBLayer_from_file():
    layer = PCBLayer.from_cam(read(COPPER_FILE))
    assert isinstance(layer, PCBLayer)
    layer = PCBLayer.from_cam(read(NCDRILL_FILE))
    assert isinstance(layer, DrillLayer)
    layer = PCBLayer.from_cam(read(NETLIST_FILE))
    assert isinstance(layer, PCBLayer)
    assert layer.layer_class == "ipc_netlist"


def test_PCBLayer_bounds():
    source = read(COPPER_FILE)
    layer = PCBLayer.from_cam(source)
    assert source.bounds == layer.bounds


def test_DrillLayer_from_cam():
    no_exceptions = True
    try:
        layer = DrillLayer.from_cam(read(NCDRILL_FILE))
        assert isinstance(layer, DrillLayer)
    except:
        no_exceptions = False
    assert no_exceptions
