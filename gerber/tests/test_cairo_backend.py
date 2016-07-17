#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Garret Fick <garret@ficksworkshop.com>
import io
import os

from ..render.cairo_backend import GerberCairoContext
from ..rs274x import read, GerberFile
from .tests import *


TWO_BOXES_FILE = os.path.join(os.path.dirname(__file__),
                                'resources/example_two_square_boxes.gbr')
TWO_BOXES_EXPECTED = os.path.join(os.path.dirname(__file__),
                                'golden/example_two_square_boxes.png')

def test_render_polygon():

    _test_render(TWO_BOXES_FILE, TWO_BOXES_EXPECTED)

def _test_render(gerber_path, png_expected_path, create_output_path = None):
    """Render the gerber file and compare to the expected PNG output.
    
    Parameters
    ----------
    gerber_path : string
        Path to Gerber file to open
    png_expected_path : string
        Path to the PNG file to compare to
    create_output : string|None
        If not None, write the generated PNG to the specified path.
        This is primarily to help with 
    """
    
    gerber = read(gerber_path)

    # Create PNG image to the memory stream
    ctx = GerberCairoContext()
    gerber.render(ctx)

    actual_bytes = ctx.dump(None)
    
    # If we want to write the file bytes, do it now. This happens
    if create_output_path:
        with open(create_output_path, 'wb') as out_file:
            out_file.write(actual_bytes)
        # Creating the output is dangerous - it could overwrite the expected result.
        # So if we are creating the output, we make the test fail on purpose so you
        # won't forget to disable this
        assert_false(True, 'Test created the output %s. This needs to be disabled to make sure the test behaves correctly' % (create_output_path,))
    
    # Read the expected PNG file
    
    with open(png_expected_path, 'rb') as expected_file:
        expected_bytes = expected_file.read()
    
    assert_equal(expected_bytes, actual_bytes)
