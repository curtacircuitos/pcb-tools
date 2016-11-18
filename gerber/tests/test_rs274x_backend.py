#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Garret Fick <garret@ficksworkshop.com>

import os

from ..render.rs274x_backend import Rs274xContext
from ..rs274x import read
from .tests import *

def test_render_two_boxes():
    """Umaco exapmle of two boxes"""
    _test_render('resources/example_two_square_boxes.gbr', 'golden/example_two_square_boxes.gbr')


def _test_render_single_quadrant():
    """Umaco exapmle of a single quadrant arc"""

    # TODO there is probably a bug here
    _test_render('resources/example_single_quadrant.gbr', 'golden/example_single_quadrant.gbr')


def _test_render_simple_contour():
    """Umaco exapmle of a simple arrow-shaped contour"""
    _test_render('resources/example_simple_contour.gbr', 'golden/example_simple_contour.gbr')


def _test_render_single_contour_1():
    """Umaco example of a single contour

    The resulting image for this test is used by other tests because they must generate the same output."""
    _test_render('resources/example_single_contour_1.gbr', 'golden/example_single_contour.gbr')


def _test_render_single_contour_2():
    """Umaco exapmle of a single contour, alternate contour end order

    The resulting image for this test is used by other tests because they must generate the same output."""
    _test_render('resources/example_single_contour_2.gbr', 'golden/example_single_contour.gbr')


def _test_render_single_contour_3():
    """Umaco exapmle of a single contour with extra line"""
    _test_render('resources/example_single_contour_3.gbr', 'golden/example_single_contour_3.gbr')


def _test_render_not_overlapping_contour():
    """Umaco example of D02 staring a second contour"""
    _test_render('resources/example_not_overlapping_contour.gbr', 'golden/example_not_overlapping_contour.gbr')


def _test_render_not_overlapping_touching():
    """Umaco example of D02 staring a second contour"""
    _test_render('resources/example_not_overlapping_touching.gbr', 'golden/example_not_overlapping_touching.gbr')


def _test_render_overlapping_touching():
    """Umaco example of D02 staring a second contour"""
    _test_render('resources/example_overlapping_touching.gbr', 'golden/example_overlapping_touching.gbr')


def _test_render_overlapping_contour():
    """Umaco example of D02 staring a second contour"""
    _test_render('resources/example_overlapping_contour.gbr', 'golden/example_overlapping_contour.gbr')


def _DISABLED_test_render_level_holes():
    """Umaco example of using multiple levels to create multiple holes"""

    # TODO This is clearly rendering wrong. I'm temporarily checking this in because there are more
    # rendering fixes in the related repository that may resolve these.
    _test_render('resources/example_level_holes.gbr', 'golden/example_overlapping_contour.gbr')


def _DISABLED_test_render_cutin():
    """Umaco example of using a cutin"""

    # TODO This is clearly rendering wrong.
    _test_render('resources/example_cutin.gbr', 'golden/example_cutin.gbr')


def _test_render_fully_coincident():
    """Umaco example of coincident lines rendering two contours"""

    _test_render('resources/example_fully_coincident.gbr', 'golden/example_fully_coincident.gbr')


def _test_render_coincident_hole():
    """Umaco example of coincident lines rendering a hole in the contour"""

    _test_render('resources/example_coincident_hole.gbr', 'golden/example_coincident_hole.gbr')


def _test_render_cutin_multiple():
    """Umaco example of a region with multiple cutins"""

    _test_render('resources/example_cutin_multiple.gbr', 'golden/example_cutin_multiple.gbr')


def _test_flash_circle():
    """Umaco example a simple circular flash with and without a hole"""

    _test_render('resources/example_flash_circle.gbr', 'golden/example_flash_circle.gbr')


def _test_flash_rectangle():
    """Umaco example a simple rectangular flash with and without a hole"""

    _test_render('resources/example_flash_rectangle.gbr', 'golden/example_flash_rectangle.gbr')


def _test_flash_obround():
    """Umaco example a simple obround flash with and without a hole"""

    _test_render('resources/example_flash_obround.gbr', 'golden/example_flash_obround.gbr')


def _test_flash_polygon():
    """Umaco example a simple polygon flash with and without a hole"""

    _test_render('resources/example_flash_polygon.gbr', 'golden/example_flash_polygon.gbr')


def _test_holes_dont_clear():
    """Umaco example that an aperture with a hole does not clear the area"""

    _test_render('resources/example_holes_dont_clear.gbr', 'golden/example_holes_dont_clear.gbr')


def _test_render_am_exposure_modifier():
    """Umaco example that an aperture macro with a hole does not clear the area"""

    _test_render('resources/example_am_exposure_modifier.gbr', 'golden/example_am_exposure_modifier.gbr')


def _resolve_path(path):
    return os.path.join(os.path.dirname(__file__),
                                path)


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

    gerber_path = _resolve_path(gerber_path)
    png_expected_path = _resolve_path(png_expected_path)
    if create_output_path:
        create_output_path = _resolve_path(create_output_path)

    gerber = read(gerber_path)

    # Create GBR output from the input file
    ctx = Rs274xContext(gerber.settings)
    gerber.render(ctx)

    actual_contents = ctx.dump()

    # If we want to write the file bytes, do it now. This happens
    if create_output_path:
        with open(create_output_path, 'wb') as out_file:
            out_file.write(actual_contents.getvalue())
        # Creating the output is dangerous - it could overwrite the expected result.
        # So if we are creating the output, we make the test fail on purpose so you
        # won't forget to disable this
        assert_false(True, 'Test created the output %s. This needs to be disabled to make sure the test behaves correctly' % (create_output_path,))

    # Read the expected PNG file

    with open(png_expected_path, 'r') as expected_file:
        expected_contents = expected_file.read()

    assert_equal(expected_contents, actual_contents.getvalue())

    return gerber
