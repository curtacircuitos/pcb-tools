#!/usr/bin/env python
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
"""
CAM File Operations
===================
**Transformations and other operations performed on Gerber and Excellon files**

"""
import copy


def to_inch(cam_file):
    """ Convert Gerber or Excellon file units to imperial

    Parameters
    ----------
    cam_file : :class:`gerber.cam.CamFile` subclass
        Gerber or Excellon file to convert

    Returns
    -------
    cam_file : :class:`gerber.cam.CamFile` subclass
        A deep copy of the source file with units converted to imperial.
    """
    cam_file = copy.deepcopy(cam_file)
    cam_file.to_inch()
    return cam_file


def to_metric(cam_file):
    """ Convert Gerber or Excellon file units to metric

    Parameters
    ----------
    cam_file : :class:`gerber.cam.CamFile` subclass
        Gerber or Excellon file to convert

    Returns
    -------
    cam_file : :class:`gerber.cam.CamFile` subclass
        A deep copy of the source file with units converted to metric.
    """
    cam_file = copy.deepcopy(cam_file)
    cam_file.to_metric()
    return cam_file


def offset(cam_file, x_offset, y_offset):
    """ Offset a Cam file by a specified amount in the X and Y directions.

    Parameters
    ----------
    cam_file : :class:`gerber.cam.CamFile` subclass
        Gerber or Excellon file to offset

    x_offset : float
        Amount to offset the file in the X direction

    y_offset : float
        Amount to offset the file in the Y direction

    Returns
    -------
    cam_file : :class:`gerber.cam.CamFile` subclass
        An offset deep copy of the source file.
    """
    cam_file = copy.deepcopy(cam_file)
    cam_file.offset(x_offset, y_offset)
    return cam_file


def scale(cam_file, x_scale, y_scale):
    """ Scale a Cam file by a specified amount in the X and Y directions.

    Parameters
    ----------
    cam_file : :class:`gerber.cam.CamFile` subclass
        Gerber or Excellon file to scale

    x_scale : float
        X-axis scale factor

    y_scale : float
        Y-axis scale factor

    Returns
    -------
    cam_file : :class:`gerber.cam.CamFile` subclass
        An scaled deep copy of the source file.
    """
    # TODO
    pass


def rotate(cam_file, angle):
    """ Rotate a Cam file a specified amount about the origin.

    Parameters
    ----------
    cam_file : :class:`gerber.cam.CamFile` subclass
        Gerber or Excellon file to rotate

    angle : float
        Angle to rotate the file in degrees.

    Returns
    -------
    cam_file : :class:`gerber.cam.CamFile` subclass
        An rotated deep copy of the source file.
    """
    # TODO
    pass
