.. currentmodule:: vpype

========
Cookbook
========

..
  Laying out a SVG for plotting
  =============================

  Optimizing a SVG for plotting
  =============================

  Merging multiple designs into a multi-layer SVG
  ===============================================

  Repeating a design on a grid
  ============================




  External scripts
  ================

  The `script` command is a very useful generator that relies on an external Python script to produce geometries. Its
  use is demonstrated by the `alien.sh` and `alien2.sh` examples. A path to a Python file must be passed as argument.
  The file must implement a `generate()` function which returns a Shapely `MultiLineString` object. This is very easy
  and explained in the [Shapely documentation](https://shapely.readthedocs.io/en/latest/manual.html#collections-of-lines).





See :ref:`cmd_write` command.

.. The :ref:`vpype frame <reference#vpype-frame>` command

The :ref:`fundamentals_blocks` section.

The :py:class:`LineCollection` class.

The :option:`--single-path <write --single-path>` option.

The :doc:`plugins` pages.
