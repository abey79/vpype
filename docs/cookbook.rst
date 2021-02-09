.. currentmodule:: vpype

.. _cookbook:

========
Cookbook
========

.. highlight:: bash

Laying out a SVG for plotting
=============================

There are two ways to layout geometries on a page. The preferred way is to use commands such as :ref:`cmd_layout`, :ref:`cmd_scale`, :ref:`cmd_scaleto`, :ref:`cmd_translate`. In particular, :ref:`cmd_layout` handles most common cases
by centering the geometries on page and optionally scaling them to fit specified margins. These commands act on the pipeline and their effect can be previewed using the :ref:`cmd_show` command. The following examples all use this approach.

Alternatively, the :ref:`cmd_write` commands offers option such as :option:`--page-size <write --page-size>` and
:option:`--center <write --center>` which can also be used to layout geometries. It must be understood that these
options *only* affect the output file and leave the pipeline untouched. Their effect cannot be previewed by the
:ref:`cmd_show` command, even if it placed after the :ref:`cmd_write` command.


This command will :ref:`cmd_read` a SVG file, and then :ref:`cmd_write` it to a new SVG file sized to A4 in landscape orientation, with the design centred on the page::

  $ vpype read input.svg layout --landscape a4 write output.svg

The :ref:`cmd_layout` command implicitly centers the geometries on the page. The :ref:`cmd_pagesize` command can be used
to choose the page size without changing the geometries::

  $ vpype read input.svg pagesize --landscape a4 write output.svg

This command will :ref:`cmd_read` a SVG file and lay it out to 3cm margin with a top vertical alignment (a generally pleasing arrangement for square designs on the portrait-oriented page), and then :ref:`cmd_write` it to a new SVG::

  $ vpype read input.svg layout --fit-to-margins 3cm --valign top a4 write output.svg

This command will :ref:`cmd_read` a SVG file, :ref:`cmd_scale` it down to a 80% of its original size, and then :ref:`cmd_write` it to a new A5-sized SVG, centred on the page::

  $ vpype read input.svg scale 0.8 0.8 layout a5 write output.svg

This command will :ref:`cmd_read` a SVG file, scale it down to a 5x5cm square (using the :ref:`cmd_scaleto` command), and then :ref:`cmd_write` it to a new A5-sized SVG, centred on the page::

  $ vpype read input.svg scaleto 5cm 5cm layout a5 write output.svg

This command will :ref:`cmd_read` a SVG file, :ref:`cmd_crop` it to a 10x10cm square positioned 57mm from the top and left corners of the design, and then :ref:`cmd_write` it to a new SVG whose page size will be identical to the input SVG::

  $ vpype read input.svg crop 57mm 57mm 10cm 10cm write output.svg

This command will :ref:`cmd_read` a SVG file, add a single-line :ref:`cmd_frame` around the design, 5cm beyond its bounding box, and then :ref:`cmd_write` it to a new SVG::

  $ vpype read input.svg frame --offset 5cm write output.svg


Make a previsualisation SVG
===========================

The SVG output of :ref:`cmd_write` can be used to previsualize and inspect a plot. By default, paths are colored by layer. It can be useful to color each path differently to inspect the result of :ref:`cmd_linemerge`::

  $ vpype read input.svg linemerge write --color-mode path output.svg

Likewise, pen-up trajectories can be included in the SVG to inspect the result of :ref:`cmd_linesort`::

  $ vpype read input.svg linesort write --pen-up output.svg

Note that :option:`write --pen-up` should only be used for previsualization purposes as the pen-up trajectories may end-up being plotted otherwise. The Axidraw software will ignore the layer in which the pen-up trajectories are written, so it is safe to keep them in this particular case.


Optimizing a SVG for plotting
=============================

This command will :ref:`cmd_read` a SVG file, merge any lines whose endings are less than 0.5mm from each other with :ref:`cmd_linemerge`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linemerge --tolerance 0.5mm write output.svg

In some cases such as densely connected meshes (e.g. a grid where made of touching square paths), :ref:`cmd_linemerge` may not be able to fully optimize the plot by itself. Using :ref:`cmd_splitall` before breaks everything into its constituent segment and enables :ref:`cmd_linemerge` to perform a more aggressive optimization, at the cost of a increased processing time::

  $ vpype read input.svg splitall linemerge --tolerance 0.5mm write output.svg

This command will :ref:`cmd_read` a SVG file, simplify its geometry by reducing the number of segments in a line until they're a maximum of 0.1mm from each other using :ref:`cmd_linesimplify`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linesimplify --tolerance 0.1mm write output.svg

This command will :ref:`cmd_read` a SVG file, randomise the seam location for paths whose beginning and end points are a maximum of 0.03mm from each other with :ref:`cmd_reloop`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg reloop --tolerance 0.03mm write output.svg

This command will :ref:`cmd_read` a SVG file, extend each line with a mirrored copy of itself three times using :ref:`cmd_multipass`, and then :ref:`cmd_write` a new SVG file. This is useful for pens that need a few passes to get a good result::

  $ vpype read input.svg multipass --count 3 write output.svg

This command will :ref:`cmd_read` a SVG file, use :ref:`cmd_linesort` to sort the lines to minimise pen-up travel distance, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linesort write output.svg


Merging multiple designs into a multi-layer SVG
===============================================

This command will :ref:`cmd_read` two SVG files onto two different layers, then :ref:`cmd_write` them into a single SVG
file::

  $ vpype read --single-layer --layer 1 input1.svg read --single-layer --layer 2 input2.svg write output.svg

Note the use of :option:`--single-layer <read --single-layer>`. It is necessary to make sure that the input SVG is
merged into a single layer and is necessary to enable the :option:`--layer <read --layer>` option.

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
plotter to plotter and even for different physical paper format, the plotter model must be provided
to the :ref:`cmd_write` command::

  $ vpype read input.svg write --device hp7475a output.hpgl

The plotter paper size will be inferred from the current page size (as set by the input SVG or using either the :ref:`cmd_pagesize` or :ref:`cmd_layout` commands).
The plotter type/paper format combination must exist in the built-in or user-provided configuration file. See
:ref:`faq_custom_hpgl_config` for information on how to create one. If a matching plotter paper size cannot be found,
an error will be generated. In this case, the paper size must manually specified with the :option:`--page-size <write --page-size>` option::

  $ vpype read input.svg write --device hp7475a --page-size a4 --landscape output.hpgl

Here the :option:`--landscape <write --landscape>` is also used to indicate that landscape orientation is desired. As
for SVG output, the :option:`--center <write --center>` is often use to center the geometries in the middle of the page.

It is typically useful to optimize the input SVG during the conversion. The following example is typical of real-world
use::

  $ vpype read input.svg linesimplify reloop linemerge linesort layout a4 write --device hp7475a output.hpgl


Defining a default HPGL plotter device
======================================

If you are using the same type of plotter regularly, it may be cumbersome to systematically add the :option:`--device
<write --device>` option to the :ref:`cmd_write` command. The default device can be set in the ``~/.vpype.toml``
configuration file by adding the following section:

  .. code-block:: toml

    [command.write]
    default_hpgl_device = "hp7475a"


.. _faq_custom_hpgl_config:

Creating a custom configuration file for a HPGL plotter
=======================================================

The configuration for a number of HPGL plotter is bundled with vpype (run ``vpype write --help`` for a list). If your
plotter is not included, it is possible to define your own plotter configuration either in `~/.vpype.toml` or any other
file. In the latter case, you must instruct vpype to load the configuration using the :option:`--config <vpype
--config>` global option::

  $ vpype --config my_config_file.toml read input.svg [...] write --device my_plotter --page-size a4 output.hpgl

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

    [[device.my_plotter.paper]]
    name = "a"                          # name of the paper format

    paper_size = ["11in", "8.5in"]      # (optional) physical paper size / CAUTION: order must
                                        # respect the native X/Y axis orientation of the plotter
                                        # unless paper_orientation is specified
                                        # Note: may be omitted if the plotter support arbitrary
                                        # paper size

    paper_orientation = "portrait"      # (optional) "portrait" or "landscape"
                                        # specify the orientation of the plotter  coordinate
                                        # system on the page ("landscape" means the X axis is
                                        # along the long edge)

    origin_location = [".5in", "8in"]   # physical location from the page's top-left corner of
                                        # the (0, 0) plotter unit coordinates

    origin_location_reference = "topleft"
                                        # (optional) reference used for origin_location
                                        # "topleft" (default) or "botleft"

    x_range = [0, 16640]                # (optional) admissible range in plotter units along
                                        # the X axis
    y_range = [0, 10365]                # (optional) admissible range in plotter units along
                                        # the Y axis
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
  that ``origin_location`` is measured from the bottom-left corner, unless ``origin_location_reference`` is set to
  ``"botleft"``.


Using arbitrary paper size with HPGL output
===========================================

Some plotters such as the Calcomp Designmate support arbitrary paper sizes. Exporting HPGL with arbitrary paper size
requires a specific paper configuration. vpype ships with the ``flex`` and ``flexl`` configurations for the
Designmate, which can serve as examples to create configurations for other plotters.

For arbitrary paper size, the paper configuration must omit the ``paper_size`` parameter and specify a value for
``paper_orientation``. Here is the ``flexl`` configuration for the Designmate when paper is loaded in landscape
orientation in the plotter:

  .. code-block:: toml

    [[device.designmate.paper]]
    name = "flexl"
    y_axis_up = true
    paper_orientation = "landscape"
    origin_location = ["15mm", "15mm"]
    origin_location_reference = "botleft"
    rotate_180 = true
    final_pu_params = "0,0"

Note the missing ``paper_size``, as well as the values for ``paper_orientation`` and ``origin_location_reference``.

When using arbitrary paper size, the paper size is assumed to be identical to the current page size as set by the
:ref:`cmd_read`, :ref:`cmd_pagesize`, or :ref:`cmd_layout` commands. Here is a typical example of use::

  $ vpype read input.svg layout --fit-to-margins 3cm 30x50cm write -d designmate -p flexl output.hpgl

In this case, the page size is set by the :ref:`cmd_layout` command (30x50cm) and the :ref:`cmd_write` command is set to
use the ``flexl`` paper configuration because the paper is loaded in landscape orientation in the plotter. If the input
SVG is already sized and laid out according to the paper size, the :ref:`cmd_layout` command may be omitted.


Batch processing many SVG with bash scripts and ``parallel``
============================================================

Computers offer endless avenues for automation, which depend on OS and the type of task at hand. Here is one way to
easily process a large number of SVG with the same vpype pipeline. This approach relies on the
`GNU Parallel <https://www.gnu.org/software/parallel/>`_ software and is best suited to Unix/Linux/macOS computers.
Thanks to ``parallel``, this approach takes advantage of all available processing cores.

This is an example that illustrates the general idea::

  $ parallel --plus vpype read {} linemerge linesort write {/.svg/_processed.svg} ::: *.svg

Let's break down how this works:

  * ``GNU parallel`` will execute the command before the ``:::`` maker for each argument it finds after the marker. In this example, we used ``*.svg`` which expends to the list of SVG files in the current directory.
  * The marker ``{}`` is replaced by ``GNU parallel`` with the current item being processed (e.g. the current SVG file).
  * The marker ``{/.svg/_processed.svg}`` does the same but it replaces ``.svg`` by ``_processed.svg``. This way, if one of the original SVG file is called ``my_file.svg``, it will be saved as ``my_file_processed.svg`` once processed.
  * The ``--plus`` option to ``GNU parallel`` is required to enable the string replacement syntax.

The results can easily be customised by changing one or more of these elements. When designing your own command, it is
best to start with the ``--dry-run`` option so that ``GNU parallel`` just prints the jobs instead of actually executing
them::

  $ parallel --dry-run --plus vpype read {} linemerge linesort write {/.svg/_processed.svg} ::: *.svg


Repeating a design on a grid
============================

This command will draw a collection of 3x3cm :ref:`circles <cmd_circle>` in a 5x8 grid, then :ref:`cmd_show` the results using matplotlib::

  $ vpype begin                   \
      grid 5 8                    \
      circle 0 0 3cm              \
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
