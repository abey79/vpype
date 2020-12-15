=======
*vpype*
=======

What is *vpype*?
----------------

In a nutshell, *vpype* is an extensible CLI pipeline utility which aims to be the Swiss Army knife for creating, modifying and/or optimizing plotter-ready vector graphics. Let's break this down:

- CLI: *vpype* is a command-line utility, so it is operated from a terminal
- Pipeline: *vpype* operates by assembling 'commands' in sequences in which each command generates or process geometries before passing them on to the next command. Here is an example:

    ``vpype read input.svg scale 2 2 linesort write output.svg``

  Here the geometries are loaded from a file (``read input.svg``), their size is doubled in both directions (``scale 2 2``), paths are reordered to minimize plotting time (``linesort``), and an SVG file is created with the result (``write output.svg``).
- Extensible: new commands can easily be added to *vpype* with plug-ins. This allows anyone to extend *vpype* with new commands or to write their own generative algorithm.
- Plotter vector graphics: *vpype* focuses on the niche of vector graphics for plotters (such as the `Axidraw <https://www.axidraw.com>`_) rather than being a general purpose vector processing utility.
- Swiss Army knife: *vpype* is flexible, contains many tools and its author is Swiss.


Download and install
--------------------

.. highlight:: bash

For Windows, an installer is available `here <https://github.com/abey79/vpype/releases>`_ (note: plug-ins cannot be installed
when using this installation method).

For other platforms, and when plug-ins are required, *vpype* can be installed from the `Python Package Index <https://pypi.org>`_
using the following command (Python 3.8 recommended)::

  pip install vpype

Check the :ref:`installation instructions <install>` for more details, in particular on how to use a virtual environment (recommended).

Using this documentation
------------------------

If you are of the straight-to-action type, the list of available commands is available in the :ref:`reference <reference>` section. You may also jump to the :ref:`cookbook <cookbook>` section to find a recipe that matches your need.

For a deep understanding of *vpype*, take a dive in the section on :ref:`fundamentals <fundamentals>`.

Developers can learn more about extending *vpype* in the :ref:`Creating plug-ins <plugins>` section and the :ref:`API reference <api>`.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   install
   fundamentals
   cookbook
   plugins
   contributing


Reference
---------

.. toctree::
   :maxdepth: 2

   reference
   api


Miscellaneous Pages
-------------------

.. toctree::
   :maxdepth: 2

   CHANGELOG
   license
