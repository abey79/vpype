=======
*vpype*
=======

What is *vpype*?
----------------

In a nutshell, *vpype* is an extensible CLI pipeline utility which aims to be the Swiss Army knife for creating, modifying and/or optimizing plotter-ready vector graphics. Let's break this down:

- CLI: *vpype* is a command-line utility, so it is operated from a terminal
- Pipeline: *vpype* operates by assembling 'commands' in sequences in which each command generates or process geometries before passing them on to the next command. Here is an example:

    ```vpype read input.svg scale 2 2 linesort write output.svg```

  Here the geometries are loaded from a file (``read input.svg``), their size is doubled in both directions (``scale 2 2``), paths are reordered to minimize plotting time (``linesort``), and a SVG file is created with the result (``write output.svg``).
- Extensible: new commands can easily be added to *vpype* through plug-ins. This allows third parties to extend *vpype* with new commands and yourself to write your own generative algorithm in the form of *vpype* plug-ins.
- Plotter vector graphics: *vpype* focuses on the niche of vector graphics for plotters (such as the `Axidraw <https://www.axidraw.com>`_) rather than being a general purpose vector processing utility.
- Swiss Army knife: *vpype* is flexible, contains many tools and its author is Swiss.


Using this documentation
------------------------

Start with `installation instructions <install>`_ to get up and running with your installation of *vpype*.

Fro the straight-to-action type, the list of available commands is available in the `reference <reference>`_ section. You may also jump to the `cookbook <cookbook>`_ section to find a recipe that matches your need.

For a deep understanding of *vpype*, take a dive in the section on `fundamentals <fundamentals>`_.

Developers can learn more about extending *vpype* in the `Creating plug-ins <plugin>`_ section and the `API reference <api>`_.

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

   license
