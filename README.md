gerber-tools
============
![Travis CI Build Status](https://travis-ci.org/hamiltonkibbe/gerber-tools.svg?branch=master) 
[![Coverage Status](https://coveralls.io/repos/hamiltonkibbe/gerber-tools/badge.png?branch=master)](https://coveralls.io/r/hamiltonkibbe/gerber-tools?branch=master)

Tools to handle Gerber and Excellon files in Python.

Example:

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


Rendering:
![Composite Top Image](examples/composite_top.png)
![Composite Bottom Image](examples/composite_bottom.png)