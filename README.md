pcb-tools
============
[![Travis CI Build Status](https://travis-ci.org/curtacircuitos/pcb-tools.svg?branch=master)](https://travis-ci.org/curtacircuitos/pcb-tools)
[![Coverage Status](https://coveralls.io/repos/curtacircuitos/pcb-tools/badge.png?branch=master)](https://coveralls.io/r/curtacircuitos/pcb-tools?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pcb-tools/badge/?version=latest)](https://readthedocs.org/projects/pcb-tools/?badge=latest)

Tools to handle Gerber and Excellon files in Python.

Usage Example:
---------------
    import gerber
    from gerber.render import GerberCairoContext

    # Read gerber and Excellon files
    top_copper = gerber.read('example.GTL')
    nc_drill = gerber.read('example.txt')

    # Rendering context
    ctx = GerberCairoContext()

    # Create SVG image
    top_copper.render(ctx)
    nc_drill.render(ctx, 'composite.svg')


Rendering Examples:
-------------------
###Top Composite rendering
![Composite Top Image](examples/cairo_example.png)
![Composite Bottom Image](examples/cairo_bottom.png)

Source code for this example can be found [here](examples/cairo_example.py).


Install from source:
```
$ git clone https://github.com/curtacircuitos/pcb-tools.git
$ cd pcb-tools
$ make
$ python setup.py install
```

Documentation:
--------------
[PCB Tools Documentation](http://pcb-tools.readthedocs.org/en/latest/)
