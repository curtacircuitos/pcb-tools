#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Hamilton Kibbe <ham@hamiltonkib.be>

from nose.tools import assert_in
from nose.tools import assert_not_in
from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_almost_equal
from nose.tools import assert_true
from nose.tools import assert_false
from nose.tools import assert_raises
from nose.tools import raises
from nose import with_setup

__all__ = ['assert_in', 'assert_not_in', 'assert_equal', 'assert_not_equal',
           'assert_almost_equal', 'assert_array_almost_equal', 'assert_true',
           'assert_false', 'assert_raises', 'raises', 'with_setup']


def assert_array_almost_equal(arr1, arr2, decimal=6):
    assert_equal(len(arr1), len(arr2))
    for i in range(len(arr1)):
        assert_almost_equal(arr1[i], arr2[i], decimal)
