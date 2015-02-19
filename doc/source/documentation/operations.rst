:mod:`operations` --- Cam File operations
=========================================

.. module:: operations
   :synopsis: Functions for modifying CAM files
.. sectionauthor:: Hamilton Kibbe <ham@hamiltonkib.be>


The :mod:`operations` module provides functions which modify
:class:`gerber.cam.CamFile` objects. All of the functions in this module
return a modified copy of the supplied file.

.. _operations-contents:

Functions
---------
The :mod:`operations` module defines the following functions:

.. autofunction:: gerber.operations.to_inch
.. autofunction:: gerber.operations.to_metric
.. autofunction:: gerber.operations.offset



