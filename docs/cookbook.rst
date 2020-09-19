.. currentmodule:: vpype

.. _cookbook:

========
Cookbook
========


Laying out a SVG for plotting
=============================

This command will :ref:`cmd_read` an SVG file, and then :ref:`cmd_write` it to a new SVG file sized to A4 portrait::

  $ vpype read input.svg write --page-format a4 output.svg

This command will :ref:`cmd_read` an SVG file, and then :ref:`cmd_write` it to a new SVG file sized to 13x9in, rotated to landscape, with the design centred on the page::

  $ vpype read input.svg write --page-format 13x9in --landscape --center output.svg

This command will :ref:`cmd_read` a multilayered SVG file, flatten it by converting all layers to a single layer, and then :ref:`cmd_write` it to a new SVG with the boundaries fitted tightly around the design::

  $ vpype read --single-layer input.svg write output.svg

This command will :ref:`cmd_read` an SVG file, convert all paths to a single compound path, and then :ref:`cmd_write` it to a new SVG with the boundaries fitted tightly around the design::

  $ vpype read input.svg write --single-path output.svg

This command will :ref:`cmd_read` an SVG file, :ref:`cmd_scale` it down to a 80% of its original size, and then :ref:`cmd_write` it to a new A5-sized SVG, centred on the page::

  $ vpype read input.svg scale 0.8 0.8 write output.svg

This command will :ref:`cmd_read` an SVG file, scale it down to a 5x5cm square (using the :ref:`cmd_scaleto` command), and then :ref:`cmd_write` it to a new A5-sized SVG, centred on the page::

  $ vpype read input.svg scaleto 5cm 5cm write --page-format a5 --center output.svg

This command will :ref:`cmd_read` an SVG file, :ref:`cmd_crop` it to a 10x10cm square positioned 57mm from the top and left corners of the design, and then :ref:`cmd_write` it to a new SVG::

  $ vpype read input.svg crop 57mm 57mm 10cm 10cm write output.svg

This command will :ref:`cmd_read` an SVG file, add a single-line :ref:`cmd_frame` around the design, 5cm beyond its bounding box, and then :ref:`cmd_write` it to a new SVG::

  $ vpype read input.svg frame --offset 5cm write output.svg


Make a previsualisation SVG
===========================

The SVG output of :ref:`cmd_write` can be used to previsualize and inspect a plot. By default, paths are colored by layer. It can be useful to color each path differently to inspect the result of :ref:`cmd_linemerge`::

  $ vpype read input.svg linemerge write --color-mode path output.svg

Likewise, pen-up trajectories can be included in the SVG to inspect the result of :ref:`cmd_linesort`::

  $ vpype read input.svg linesort write --pen-up output.svg

Note that :option:`write --single-path` should only be used for previsualization purposes as the pen-up trajectories may end-up being plotted otherwise. The Axidraw software will ignore the layer in which the pen-up trajectories are written, so it is safe to keep them in this particular case.


Optimizing a SVG for plotting
=============================

This command will :ref:`cmd_read` an SVG file, merge any lines whose endings are less than 0.5mm from each other with :ref:`cmd_linemerge`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linemerge --tolerance 0.5mm write output.svg

In some cases such as densely connected meshes (e.g. a grid where made of touching square paths), :ref:`cmd_linemerge` may not be able to fully optimize the plot by itself. Using :ref:`cmd_splitall` before breaks everything into its constituent segment and enables :ref:`cmd_linemerge` to perform a more aggressive optimization, at the cost of a increased processing time::

  $ vpype read input.svg splitall linemerge --tolerance 0.5mm write output.svg

This command will :ref:`cmd_read` an SVG file, simplify its geometry by reducing the number of segments in a line until they're a maximum of 0.1mm from each other using :ref:`cmd_linesimplify`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linesimplify --tolerance 0.1mm write output.svg

This command will :ref:`cmd_read` an SVG file, randomise the seam location for paths whose beginning and end points are a maximum of 0.03mm from each other with :ref:`cmd_reloop`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg reloop --tolerance 0.03mm write output.svg

This command will :ref:`cmd_read` an SVG file, extend each line with a mirrored copy of itself three times using :ref:`cmd_multipass`, and then :ref:`cmd_write` a new SVG file. This is useful for pens that need a few passes to get a good result::

  $ vpype read input.svg multipass --count 3 write output.svg

This command will :ref:`cmd_read` an SVG file, use :ref:`cmd_linesort` to sort the lines to minimise pen-up travel distance, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linesort write output.svg


Merging multiple designs into a multi-layer SVG
===============================================

This command will :ref:`cmd_read` two SVG files onto two different layers, then :ref:`cmd_write` them into a single SVG file::

  $ vpype read -m --layer 1 input1.svg read -m --layer 2 input2.svg write output.svg

This command will :ref:`cmd_read` two SVG files onto two different layers, rotate one layer 180 degrees, then :ref:`cmd_write` both layers into a single SVG file::

  $ vpype read -m --layer 1 input1.svg read -m --layer 2 input2.svg rotate --layer 2 180 write output.svg

This command will :ref:`cmd_read` two SVG files onto two different layers, :ref:`cmd_translate` (i.e. move) one of them 0.1cm down and to the right, and then :ref:`cmd_write` both layers into a single SVG file with custom layer names "Pen 1" and "Pen 2"::

 $ vpype read -m --layer 1 input1.svg read -m --layer 2 input2.svg translate --layer 2 0.1cm 0.1cm write --layer-label "Pen %d" output.svg


Repeating a design on a grid
============================

This command will draw a collection of 3x3cm :ref:`circles <cmd_circle>` in a 5x8 grid, then :ref:`cmd_show` the results using matplotlib::

  $ vpype begin                   \
      grid 5 8                    \
      circle 0 0 3cm 3cm          \
    end                           \
    show


External scripts
================

The :ref:`cmd_script` command is a very useful generator that relies on an external Python script to produce geometries. Its
use is demonstrated by the `alien.sh` and `alien2.sh` examples. A path to a Python file must be passed as argument.
The file must implement a `generate()` function which returns a Shapely `MultiLineString` object. This is very easy
and explained in the [Shapely documentation](https://shapely.readthedocs.io/en/latest/manual.html#collections-of-lines).



..
  This are example of how to refer to commands, sections, etc.:

  See :ref:`cmd_write` command.

  The :ref:`fundamentals_blocks` section.

  The :py:class:`LineCollection` class.

  The :option:`--single-path <write --single-path>` option.

  The :doc:`plugins` pages.
