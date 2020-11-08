.. currentmodule:: vpype

.. _cookbook:

========
Cookbook
========

.. highlight:: bash

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

This command will :ref:`cmd_read` two SVG files onto two different layers, then :ref:`cmd_write` them into a single SVG
file::

  $ vpype read --single-layer --layer 1 input1.svg read --single-layer --layer 2 input2.svg write output.svg

Note the use of ``--single-layer``. It is necessary to make sure that the input SVG is merged into a single layer and is
necessary to enable the ``--layer`` option.

This command will :ref:`cmd_read` two SVG files onto two different layers, rotate one layer 180 degrees, then
:ref:`cmd_write` both layers into a single SVG file::

  $ vpype read --single-layer --layer 1 input1.svg read --single-layer --layer 2 input2.svg rotate --layer 2 180 write output.svg

This command will :ref:`cmd_read` two SVG files onto two different layers, :ref:`cmd_translate` (i.e. move) one of them
0.1cm down and to the right, and then :ref:`cmd_write` both layers into a single SVG file with custom layer names
"Pen 1" and "Pen 2"::

  $ vpype read --single-layer --layer 1 input1.svg read --single-layer --layer 2 input2.svg translate --layer 2 0.1cm 0.1cm write --layer-label "Pen %d" output.svg


Filtering out small lines
=========================

In some cases (for example when using Blender's freestyle renderer), SVG files can contain a lot of tiny lines which
significantly increase the plotting time and may be detrimental to the final look. These small lines can easily be
removed thanks to the :ref:`cmd_filter` command::

  $ vpype read input.svg filter --min-length 0.5mm write output.svg


Converting a SVG to HPGL
========================

For vintage plotters, the :ref:`cmd_write` command is capable of generating HPGL code instead of SVG. HPGL output format
is automatically selected if the output path file extension is ``.hpgl``. Since HPGL coordinate systems vary widely from
plotter to plotter and even for different physical paper format, the plotter model and the paper format must be provided
to the :ref:`cmd_write` command::

  $ vpype read input.svg write --device hp7475a --page-format a4 --landscape --center output.hpgl

The plotter type/paper format combination must exist in the built-in or user-provided configuration file. See
:ref:`faq_custom_hpgl_config` for information on how to create one.

It is typically useful to optimize the input SVG during the conversion. The following example is typical of real-world
use::

  $ vpype read input.svg linesimplify reloop linemerge linesort write --device hp7475a --page-format a4 output.hpgl


Defining a default HPGL plotter device
======================================

If you are using the same type of plotter regularly, it may be cumbersome to systematically add the ``--device`` option
to the :ref:`cmd_write` command. The default device can be set in the ``~/.vpype.toml`` configuration file by adding the
following section:

  .. code-block:: toml

    [command.write]
    default_hpgl_device = "hp7475a"


.. _faq_custom_hpgl_config:

Creating a custom configuration file for a HPGL plotter
=======================================================

The configuration for a number of HPGL plotter is bundled with vpype (run ``vpype write --help`` for a list). If your
plotter is not included, it is possible to define your own plotter configuration either in `~/.vpype.toml` or any other
file. In the latter case, you must instruct vpype to load the configuration using the ``--config`` option::

  $ vpype --config my_config_file.toml read input.svg [...] write --device my_plotter --page-format a4 output.hpgl

The configuration file must first include a plotter section with the following format:

  .. code-block:: toml

    [device.my_plotter]
    name = "My Plotter"                 # human-readable name for the plotter
    plotter_unit_length = "0.02488mm"   # numeric values in pixel or string with units
    pen_count = 6                       # number of pen supported by the plotter

    info = "Plot configuration..."      # (optional) human-readable information on how
                                        # the plotter must be configured for this
                                        # configuration to work as expected

In the configuration file, all numerical values are in CSS pixel unit (1/96th of an inch). Alternatively, strings
containing the numerical value with a unit can be used and will be correctly interpreted.

Then, the configuration file must include one ``paper`` section for each paper format supported by the plotter:

  .. code-block:: toml

    [[device.my_plotter.paper]]         # note the double brackets!
    name = "a"                          # name of the paper format

    paper_size = ["11in", "8.5in"]      # physical paper size / CAUTION: order must respect
                                        # the native X/Y axis orientation of the plotter

    origin_location = [".5in", "8in"]   # physical location from the page's top-left corner of
                                        # the (0, 0) plotter unit coordinates

    x_range = [0, 16640]                # admissible range in plotter units along the X axis
    y_range = [0, 10365]                # admissible range in plotter units along the Y axis
    y_axis_up = true                    # set to true if the plotter's Y axis points up on
                                        # the physical page
    rotate_180 = true                   # (optional) set to true to rotate the geometries by
                                        # 180 degrees on the page

    aka_names = ["ansi_a", "letter"]    # (optional) name synonyms that will be recognised by
                                        # the `--paper-format` option of the `write` command

    set_ps = 0                          # (optional) if present, a PS command with the
                                        # corresponding value is generated

    final_pu_params = "0,0"             # (optional) if present, specifies parameter to pass
                                        # to the final `PU;` command

    info = "Paper loading..."           # (optional) human-readable information on how the
                                        # paper must be loaded for this configuration to work
                                        # as expected


While most of the parameters above are self-explanatory or easy to understand from the comments, there are several
aspects that require specific caution:

* ``paper_size`` *must* be defined in the order corresponding to the plotter's native X/Y axis orientation. In the
  example above, the long side is specified before the short side because the plotter's native coordinate system has
  its X axis oriented along the long side the Y axis oriented along the short side of the page.
* ``origin_location`` defines the physical location of (0, 0) plotter unit coordinate on the page, with respect to the
  top-left corner of the page in the orientation implied by ``paper_size``. In the example above, since the long edge
  is defined first, ``origin_location`` is defined based on the top-left corner in landscape orientation.
* ``y_axis_up`` defines the orientation of the plotter's native Y axis. Note that a value of ``true`` does **not** imply
  that ``origin_location`` is measured from the bottom-left corner.


Batch processing many SVG with bash scripts and ``parallel``
============================================================

Computers offer endless avenues for automation, which depend on OS and the type of task at hand. Here is one way to
easily process a large number of SVG with the same vpype pipeline. This approach relies on a  bash script and the
`GNU Parallel <https://www.gnu.org/software/parallel/>`_ software and is best suited to Unix/Linux/macOS computers.
Thanks to ``parallel``, it takes advantage of all the processing cores available.

The first step is create a script to generate all the vpype commands corresponding to each of the SVG file to process::

  #!/bin/bash

  # Loop over all the files
  for file in *.svg; do
    echo "Processing $file"
    # edit the following line with the exact command you want to run
    echo vpype read "$file" linemerge linesort  write -p a4 -c processed/"$file" >> batch.txt
  done

Name this file ``create_batch.sh``, move it next to your SVG files, and make it executable with the following command::

  $ chmod +x create_batch.sh

You can then execute it::

  $ ./create_batch.sh

This script will create a new file called ``batch.txt`` which contains all the vpype commands to be executed, one per
line. It can be opened in a text editor to verify that everything is as it should Finally, use the ``parallel`` command
(which you must first install on your computer) to execute everything using all available processing cores::

  $ parallel < batch.txt

The processed files will be saved in the ``processed`` sub-directory.


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
