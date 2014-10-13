:mod:`excellon` --- Excellon file handling
==============================================

.. module:: excellon
   :synopsis: Functions and classes for handling Excellon files
.. sectionauthor:: Hamilton Kibbe <ham@hamiltonkib.be>


The Excellon format is the most common format for exporting PCB drill
information. The Excellon format is used to program CNC drilling macines for
drilling holes in PCBs. As such, excellon files are sometimes refererred to as
NC-drill files.  The Excellon format reference is available 
`here <http://www.excellon.com/manuals/program.htm>`_. The :mod:`excellon`
submodule implements calsses to read and write excellon files without having
to know the precise details of the format.

The :mod:`excellon` submodule's :func:`read` function serves as a
simple interface for parsing excellon files.  The :class:`ExcellonFile` class
stores all the information contained in an Excellon file allowing the file to
be analyzed, modified, and updated. The :class:`ExcellonParser` class is used
in the background for parsing RS-274X files.

.. _excellon-contents:

Functions
---------
The :mod:`excellon` module defines the following functions:

.. autofunction:: gerber.excellon.read
    

Classes
-------
The :mod:`excellon` module defines the following classes:

.. autoclass:: gerber.excellon.ExcellonFile
    :members:
    

.. autoclass:: gerber.excellon.ExcellonParser
    :members:
    