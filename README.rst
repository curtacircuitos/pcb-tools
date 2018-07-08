pcb-tools
=========

|buildstatus| |coverage| |docstatus|

.. |buildstatus| image:: https://travis-ci.org/curtacircuitos/pcb-tools.svg?branch=master
   :alt: Travis CI Build Status
   :target: https://travis-ci.org/curtacircuitos/pcb-tools

.. |coverage| image:: https://coveralls.io/repos/curtacircuitos/pcb-tools/badge.png?branch=master
   :alt: Coverage Status
   :target: https://coveralls.io/r/curtacircuitos/pcb-tools?branch=master


.. |docstatus| image:: https://readthedocs.org/projects/pcb-tools/badge/?version=latest
   :alt: Documentation Status
   :target: https://readthedocs.org/projects/pcb-tools/?badge=latest

Tools to handle Gerber and Excellon files in Python.

Usage Example:
---------------

.. code:: python

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


Rendering Examples
-------------------

Top Composite rendering
~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://raw.githubusercontent.com/curtacircuitos/pcb-tools/master/examples/cairo_example.png
   :alt: Composite Top Image

Bottom Composite rendering
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. image:: https://raw.githubusercontent.com/curtacircuitos/pcb-tools/master/examples/cairo_bottom.png
   :alt: Composite Bottom Image

Source code for this example can be found `on github`_.

.. _`on github`: https://github.com/curtacircuitos/pcb-tools/blob/master/examples/cairo_example.py


Install from source:

.. code:: sh

        $ git clone https://github.com/curtacircuitos/pcb-tools.git
        $ cd pcb-tools
        $ pip install -r requirements.txt
        $ python setup.py install

Documentation
-------------

You can find the documentation for PCB-Tools on readthedocs_.

.. _readthedocs: http://pcb-tools.readthedocs.org/en/latest/


Development and Testing
-----------------------

Dependencies for developing and testing pcb-tools are listed in test-requirements.txt. Use of a virtual environment is strongly recommended.

.. code:: sh

    $ virtualenv venv
    $ source venv/bin/activate
    (venv)$ pip install -r test-requirements.txt
    (venv)$ pip install -e .

We use nose to run pcb-tools's suite of unittests and doctests.

.. code:: sh

    (venv)$ nosetests
