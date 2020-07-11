.. currentmodule:: vpype

========
Cookbook
========


  Laying out a SVG for plotting
  =============================

  This command will `read` an SVG file, and then `write` it to a new SVG file sized to A4 portrait.
  `$ vpype read input.svg write --page-format a4 output.svg`

  This command will `read` an SVG file, and then `write` it to a new SVG file sized to 13x9in, rotated to landscape, with the design centred on the page.
  `$ vpype read input.svg write --page-format 13x9in --landscape --center output.svg`

  This command will `read` a multilayered SVG file, flatten it by converting all layers to a single layer, and then `write` it to a new SVG with the boundaries fitted tightly around the design.
  `$ vpype read --single-layer input.svg write output.svg`

  This command will `read` an SVG file, convert all paths to a single compound path, and then `write` it to a new SVG with the boundaries fitted tightly around the design.
  `$ vpype read input.svg write --single-path output.svg`

  This command will `read` an SVG file, `scale` it down to a 80% of its original size, and then `write` it to a new A5-sized SVG, centred on the page.
  `$ vpype read input.svg scale 0.8 0.8 write output.svg`

  This command will `read` an SVG file, `scale` it down to a 5x5cm square, and then `write` it to a new A5-sized SVG, centred on the page.
  `$ vpype read input.svg scale --to 5cm 5cm write output.svg`

  This command will `read` an SVG file, `crop` it to a 10x10cm square positioned 57mm from the top and left corners of the design, and then `write` it to a new SVG.
  `$ vpype read input.svg crop 57mm 57mm 10cm 10cm write output.svg`

  This command will `read` an SVG file, add a single-line `frame` around the design, 5cm beyond its bounding box, and then `write` it to a new SVG.
  `$ vpype read input.svg frame --offset 5cm write output.svg`


  Optimizing a SVG for plotting
  =============================

  This command will `read` an SVG file, merge any lines whose endings are less than 0.5mm from each other with `linemerge`, and then `write` a new SVG file.
  `$ vpype read input.svg linemerge --tolerance 0.5mm write output.svg`

  This command will `read` an SVG file, simplify its geometry by reducing the number of segments in a line until they're a maximum of 0.1mm from each other using `linesimplify`, and then `write` a new SVG file.
  `$ vpype read input.svg linesimplify --tolerance 0.1mm write output.svg`

  This command will `read` an SVG file, randomise the seam location for paths whose beginning and end points are a maximum of 0.03mm from each other with `reloop`, and then `write` a new SVG file.
  `$ vpype read input.svg reloop --tolerance 0.03mm write output.svg`

  This command will `read` an SVG file, extend each line with a mirrored copy of itself three times using `multipass`, and then `write` a new SVG file. This is useful for pens that need a few passes to get a good result.
  `$ vpype read input.svg multipass --count 3 write output.svg`

  This command will `read` an SVG file, use `linesort` to sort the lines to minimise pen-up travel distance, and then `write` a new SVG file.
  `$ vpype read input.svg linesort write output.svg`


  Merging multiple designs into a multi-layer SVG
  ===============================================

  This command will `read` two SVG files onto two different layers, then `write` them into a single SVG file.
  `$ vpype read input1.svg --layer 1 read input2.svg --layer 2 write output.svg`

  This command will `read` two SVG files onto two different layers, rotate one layer 180 degrees, then `write` both layers into a single SVG file.
  `$ vpype read input1.svg --layer 1 read input2.svg --layer 2 rotate --layer 2 180 write output.svg`

  This command will `read` two SVG files onto two different layers, `translate` (i.e. move) one of them 0.1cm down and to the right, and then `write both layers into a single SVG file with custom layer names "Pen 1" and "Pen 2"  
  `$ vpype read input1.svg --layer 1 read input2.svg --layer 2 translate --layer 2 0.1cm 0.1cm write --layer-label “Pen %d” output.svg`

  Repeating a design on a grid
  ============================
  This command will draw a collection of 3x3cm `circle`s in a 5x8 grid, then `show` the results using matplotlib.
  `
  $ vpype begin                   \
      grid 5 8                    \
      circle 0 0 3cm 3cm          \
    end                           \
    show
  `

.. 

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




Here are links to :ref:`section1` and :ref:`section2`.

.. mytest:: section1

Section 1 content.


.. _section2:

section2
========

Section 2 content.