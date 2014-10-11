:mod:`gerber` --- RS-274X file handling
==============================================

.. module:: gerber
   :synopsis: Functions and classes for handling RS-274X  files
.. sectionauthor:: Hamilton Kibbe <ham@hamiltonkib.be>


The RS-274X (Gerber) format is the most common format for exporting PCB
artwork.  The Specification is published by Ucamco and is available
`here <http://www.ucamco.com/files/downloads/file/81/the_gerber_file_format_specification.pdf>`_.
The :mod:`gerber` submodule implements calsses to read and write
RS-274X files without having to know the precise details of the format.

The :mod:`gerber` submodule's :func:`read` function serves as a
simple interface for parsing gerber files.  The :class:`GerberFile` class
stores all the information contained in a gerber file allowing the file to be
analyzed, modified, and updated. The :class:`GerberParser` class is used in
the background for parsing RS-274X files.

.. _gerber-contents:
Functions
---------
The :mod:`gerber` module defines the following functions:

.. autofunction:: gerber.gerber.read

Classes
-------
The :mod:`gerber` module defines the following classes:

.. autoclass:: gerber.gerber.GerberFile
    :members:

.. autoclass:: gerber.gerber.GerberParser                                 
    :members: