pcb-tools
============
[![Travis CI Build Status](https://travis-ci.org/curtacircuitos/pcb-tools.svg?branch=master)](https://travis-ci.org/curtacircuitos/pcb-tools)
[![Coverage Status](https://coveralls.io/repos/curtacircuitos/pcb-tools/badge.png?branch=master)](https://coveralls.io/r/curtacircuitos/pcb-tools?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pcb-tools/badge/?version=latest)](https://readthedocs.org/projects/pcb-tools/?badge=latest)

Tools to handle Gerber and Excellon files in Python.

Useage Example:
---------------
    import gerber
    from gerber.render import GerberSvgContext

    # Read gerber and Excellon files
    top_copper = gerber.read('example.GTL')
    nc_drill = gerber.read('example.txt')

    # Rendering context
    ctx = GerberSvgContext()

    # Create SVG image
    top_copper.render(ctx)
    nc_drill.render(ctx, 'composite.svg')


Rendering Examples:
-------------------
###Top Composite rendering
![Composite Top Image](examples/cairo_example.png)
Source code for this example can be found [here](examples/cairo_example.py).


Documentation:
--------------
[PCB Tools Documentation](http://pcb-tools.readthedocs.org/en/latest/)
