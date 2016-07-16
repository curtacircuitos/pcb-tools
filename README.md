pcb-tools
============
[![Travis CI Build Status](https://travis-ci.org/curtacircuitos/pcb-tools.svg?branch=master)](https://travis-ci.org/curtacircuitos/pcb-tools)
[![Coverage Status](https://coveralls.io/repos/curtacircuitos/pcb-tools/badge.png?branch=master)](https://coveralls.io/r/curtacircuitos/pcb-tools?branch=master)
[![Documentation Status](https://readthedocs.org/projects/pcb-tools/badge/?version=latest)](https://readthedocs.org/projects/pcb-tools/?badge=latest)

Tools to handle Gerber and Excellon files in Python.

Useage Example:
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
Source code for this example can be found [here](examples/cairo_example.py).


Documentation:
--------------
[PCB Tools Documentation](http://pcb-tools.readthedocs.org/en/latest/)


Development and Testing:
------------------------

Dependencies for developing and testing pcb-tools are listed in test-requirements.txt. Use of a virtual environment is strongly recommended.

    $ virtualenv venv
    $ source venv/bin/activate
    (venv)$ pip install -r test-requirements.txt
    (venv)$ pip install -e .

We use nose to run pcb-tools's suite of unittests and doctests.

    (venv)$ nosetests
