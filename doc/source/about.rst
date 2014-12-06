About PCB Tools
===============

PCB CAM Files
~~~~~~~~~~~~~

PCB design (artwork) files are most often stored in `Gerber` files. This is
a generic term that may refer to `RS-274X (Gerber) <http://en.wikipedia.org/wiki/Gerber_format>`_, 
`ODB++ <http://en.wikipedia.org/wiki/ODB%2B%2B>`_ , or `Excellon <http://en.wikipedia.org/wiki/Excellon_format>`_
files.  These file formats are used by the CNC equipment used to manufacutre PCBs.

PCB Tools provides a set of utilities for visualizing and working with PCB design files
in a variety of formats. PCB Tools currently supports the following file formats:

- Gerber (RS-274X)
- Excellon

with planned support for IPC-2581, IPC-D-356 Netlists, ODB++ and more.

Visualization
~~~~~~~~~~~~~~
.. image:: ../../examples/composite_top.png
   :alt: Rendering Example

The PCB Tools module provides tools to visualize PCBs and export images in a variety of formats,
including SVG and PNG.


Future Plans
~~~~~~~~~~~~
We are working on adding the following features to PCB Tools:

- Design Rules Checking
- Editing
- Panelization



