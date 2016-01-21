#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from .tests import *
from ..layers import guess_layer_class, hints


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


def test_sort_layers():
    """ Test layer ordering
    """
    pass
