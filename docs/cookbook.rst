.. currentmodule:: vpype

.. _cookbook:

========
Cookbook
========

.. highlight:: bash


SVG reading and writing recipes
===============================

.. _faq_pipeline_in_shell_script:

Wrapping a *vpype* pipeline in a shell script
---------------------------------------------

Optimizing a SVG file is quite possibly the most common use of *vpype*. It usually is done with a pipeline similar to this example::

  $ vpype read my_file.svg linemerge linesort reloop linesimplify write my_file_optimized.svg

In particular, it is rather common to name the output file after the input file, maybe with a ``_processed`` suffix.

Such a *vpype* invocation can easily be packaged in a shell script using some simple path expression. Here is the content of such a shell script::

  #!/bin/sh

  vpype read "$1" linemerge linesort reloop linesimplify \
     write "%prop.vp_source.with_stem(prop.vp_source.stem + '_processed')%_.svg"

(Shell scripts are typically named with a ``.sh`` extension and should be marked as "executable" to be used. This can be done with the ``chmod +x my_script.sh`` command.)

The script might be used as follows::

  $ ./my_script.sh /path/to/my_file.svg

The argument passed to the script is forwarded to *vpype* through the use of ``$1``. Then, the output path provided to the  :ref:`cmd_write` command corresponds to the input path, with a ``_processed`` suffix added (e.g. ``/path/to/my_file_processed.svg`` in this case). This is achieved by the ``prop.vp_source.with_stem(prop.vp_source.stem + '_processed')`` expression.


Preserve color (or other attributes) when reading SVG
-----------------------------------------------------

By default, the :ref:`cmd_read` command sorts geometries into layers based on the input SVG's top-level groups, akin to Inkscape's layers. Stroke color is preserved *only* if it is identical for every geometries within a layer.

When preserving the color is desirable, the :ref:`cmd_read` command can sort geometries by colors instead of by top-level groups. This is achieved by using the :option:`--attr <read --attr>` option::

  $ vpype read --attr stroke input.svg [...]

Here, we tell the :ref:`cmd_read` command to sort geometry by ``stroke``, which is the SVG attribute that defines the color of an element. As a result, a layer will be created for each different color encountered in the input SVG file.

The same applies for any SVG attributes, even those not explicitly supported by *vpype*. For example, ``--attr stroke-width`` will sort layers by stroke width and ``--attr stroke-dasharray`` by type of stroke dash pattern.

Multiple attributes can even be provided::

  $ vpype read --attr stroke --attr stroke-width input.svg [...]

In this case, a layer will be created for each unique combination of color and stroke width.

.. _faq_files_to_layer:

Merge multiple SVGs into a multilayer file
------------------------------------------

This command will :ref:`cmd_read` two SVG files onto two different layers, then :ref:`cmd_write` them into a single SVG
file::

  $ vpype \
      forfile "*.svg" \
        read --layer %_i% %_path% \
      end \
      write output.svg


.. _faq_merge_layers_by_name:

Load multiple files, merging their layers by name
-------------------------------------------------

Let us consider a collection of SVG files, each with one or more named layer(s). It could be for example a collection of CMYK SVGs, some of which with all four layers, but other with a sub-set of the layers (say, only "yellow" and "black"). This recipe shows how to load these files, making sure identically-named layers are properly merged.

Here is the full pipeline::

  $ vpype \
      eval "names={};n=100" \
      forfile "*.svg" \
          read %_path% \
          forlayer \
              eval "%if _name not in names: names[_name] = n; n = n+1%" \
              lmove %_lid% "%names[_name]%" \
          end \
      end \
      write combined.svg

This pipeline makes use of two nested blocks and some clever expressions. Let us break down how it works.

The core idea is to build a dictionary ``names`` which maps "destination" layer IDs to layer name. Destination layer IDs is where geometries will be merged, and we choose a starting layer ID value ``n`` of 100 to avoid interfering with the input file layers. At the beginning, ``names`` is an empty dictionary (``{}``). Here is how it could look at the end of a typical run:

  .. code-block:: python

     names = {
        'cyan': 100,
        'magenta': 101,
        'yellow': 102,
        'black': 103
     }

The outer block, marked by the ``forfile "*.svg"`` command, iterates over SVG files in the current directory. Each file is first read using ``read %_path%``. Then, we iterate over its layers using  the ``forlayer`` block processor.

This is where it becomes interesting. For each layer, we first test whether its name exists in the ``names`` dictionary. If not, we create a new item in the dictionary with the layer name, and assign the value of ``n``. This is the layer ID at which identically-named layers must lend. Since the layer ID ``n`` is now assigned, we increment its value for the next time an "unknown" layer name is encountered.

Now that we made sure we have a destination layer ID for the current layer's name, we can move it using the ``lmove %_lid% "%names[_name]%"`` command. Here, ``_lid`` is the current layer ID as set by ``forlayer`` and ``names[_name]`` the destination layer.

This recipe can be further augmented to arrange each file on a grid. This is covered in the :ref:`faq_merge_to_grid` receipe.


.. _faq_export_by_layers:

Saving each layer as a separate file
------------------------------------

Some plotter workflows require a different for each layer, as opposed to a single, multi-layer SVG file. For example, this is often the case for gcode input using the `vpype-gcode <https://github.com/plottertools/vpype-gcode/>`__ plug-in.

This can be achieved using the :ref:`cmd_forlayer` command::

  $ vpype read input.svg forlayer write "output_%_name or _lid%.svg" end

Here, we construct the output file name either based on the layer name if available (which :ref:`cmd_forlayer` stores in the ``_name`` variable), or on the layer ID (``_lid``) otherwise.


Make a previsualisation SVG
---------------------------

The SVG output of :ref:`cmd_write` can be used to previsualize and inspect a plot. By default, paths are colored by layer. It can be useful to color each path differently to inspect the result of :ref:`cmd_linemerge`::

  $ vpype read input.svg linemerge write --color-mode path output.svg

Likewise, pen-up trajectories can be included in the SVG to inspect the result of :ref:`cmd_linesort`::

  $ vpype read input.svg linesort write --pen-up output.svg

Note that :option:`write --pen-up` should only be used for previsualization purposes as the pen-up trajectories may end-up being plotted otherwise. The Axidraw software will ignore the layer in which the pen-up trajectories are written, so it is safe to keep them in this particular case.


Layout recipes
==============

Basic layout examples
---------------------

There are two ways to layout geometries on a page. The preferred way is to use commands such as :ref:`cmd_layout`, :ref:`cmd_scale`, :ref:`cmd_scaleto`, :ref:`cmd_translate`. In particular, :ref:`cmd_layout` handles most common cases
by centering the geometries on page and optionally scaling them to fit specified margins. These commands act on the pipeline and their effect can be previewed using the :ref:`cmd_show` command. The following examples all use this approach.

Alternatively, the :ref:`cmd_write` commands offers option such as :option:`--page-size <write --page-size>` and
:option:`--center <write --center>` which can also be used to layout geometries. It must be understood that these
options *only* affect the output file and leave the pipeline untouched. Their effect cannot be previewed by the
:ref:`cmd_show` command, even if it is placed after the :ref:`cmd_write` command.


This command will :ref:`cmd_read` a SVG file, and then :ref:`cmd_write` it to a new SVG file sized to A4 in landscape orientation, with the design centred on the page::

  $ vpype read input.svg layout --landscape a4 write output.svg

The :ref:`cmd_layout` command implicitly centers the geometries on the page. The :ref:`cmd_pagesize` command can be used
to choose the page size without changing the geometries::

  $ vpype read input.svg pagesize --landscape a4 write output.svg

This command will :ref:`cmd_read` a SVG file and lay it out to 3cm margin with a top vertical alignment (a generally pleasing arrangement for square designs on the portrait-oriented page), and then :ref:`cmd_write` it to a new SVG::

  $ vpype read input.svg layout --fit-to-margins 3cm --valign top a4 write output.svg

This command will :ref:`cmd_read` a SVG file, :ref:`cmd_scale` it down to 80% of its original size, and then :ref:`cmd_write` it to a new A5-sized SVG, centred on the page::

  $ vpype read input.svg scale 0.8 0.8 layout a5 write output.svg

This command will :ref:`cmd_read` a SVG file, scale it down to a 5x5cm square (using the :ref:`cmd_scaleto` command), and then :ref:`cmd_write` it to a new A5-sized SVG, centred on the page::

  $ vpype read input.svg scaleto 5cm 5cm layout a5 write output.svg

This command will :ref:`cmd_read` a SVG file, :ref:`cmd_crop` it to a 10x10cm square positioned 57mm from the top and left corners of the design, and then :ref:`cmd_write` it to a new SVG whose page size will be identical to the input SVG::

  $ vpype read input.svg crop 57mm 57mm 10cm 10cm write output.svg

This command will :ref:`cmd_read` a SVG file, add a single-line :ref:`cmd_frame` around the design, 5cm beyond its bounding box, and then :ref:`cmd_write` it to a new SVG::

  $ vpype read input.svg frame --offset 5cm write output.svg


Cropping and framing geometries
-------------------------------

The following pipeline can be used to crop geometries and frame them with a given margin::

  $ vpype \
      read input.svg \
      eval "m=2*cm; w, h = prop.vp_page_size" \
      crop %m% %m% "%w-2*m%" "%h-2*m%" \
      rect %m% %m% "%w-2*m%" "%h-2*m%" \
      write output.svg


.. _faq_merge_to_grid:

Laying out multiple SVGs on a grid
----------------------------------

The :ref:`cmd_grid` command can be used to layout multiple SVGs onto a regular grid. This recipe shows how.

The basic idea is covered by the following pipeline::

  $ vpype \
      eval "files=glob('*.svg')" \
      eval "cols=3; rows=ceil(len(files)/cols)" \
      grid -o 10cm 15cm "%cols%" "%rows%" \
          read --no-fail "%files[_i] if _i < len(files) else ''%" \
          layout -m 0.5cm 10x15cm \
      end \
      write combined.svg

Here are the key insights to understand how this pipeline works:

  * An expression with the ``glob()`` function (see :ref:`fundamentals_expr_builtins`) is used to create a list of files to include on the grid.
  * Another expression computes the number of rows needed to include all files, given a number of column (hard-coded to 3 in this case).
  * The :ref:`cmd_grid` command uses expressions again as argument to use the previously computed column and row count.
  * For the :ref:`cmd_read` command, multiple tricks are used. The variable ``_i`` is set by the :ref:`cmd_grid` command and corresponds to the cell counter. We use it to look up the file path to read from our file list. We must however handle the last row, which might be incomplete. This is done with a conditional expression (see :ref:`fundamentals_conditional_expr`) which returns an empty path ``''`` if the cell index is beyond the end of the file list. Normally, the :ref:`cmd_read` would fail when passed a non-existing path. This is avoided by using the ``--no-fail`` option.
  * Finally, the :ref:`cmd_layout` command fits the SVGs in the cell with a margin.

One limitation of the pipeline above is that it will merge layers by their ID, disregarding properties such as layer name or color. In some cases, this may be an issue. Depending on the nature of the input SVGs, this can be addressed by reading each file in a different layer, like in :ref:`faq_files_to_layer`. This can be done by simply adding the ``--layer %_i+1%`` option to the :ref:`cmd_read` command.

When input SVGs have layer names, they can be used to merge similarly named layers together. This is done by the following pipeline::

   $ vpype \
      eval "files=glob('*.svg')" \
      eval "cols=3; rows=ceil(len(files)/cols)" \
      eval "names={};n=100" \
      grid -o 10cm 15cm "%cols%" "%rows%" \
          read --no-fail "%files[_i] if _i < len(files) else ''%" \
          layout -m 0.5cm 10x15cm \
          forlayer \
              eval "%if _name not in names: names[_name] = n; n = n+1%" \
              lmove %_lid% "%names[_name]%" \
          end \
      end \
      write combined.svg

See :ref:`faq_merge_layers_by_name` for an explanation on how this works.

Given the number of parameters involved, it may be useful to make these pipelines interactive (see :ref:`faq_interactive_pipelines`). Using a :ref:`command file <fundamentals_command_files>` is also a nice way to make easy to reuse. Here is an example of command file::

  # Content of file grid.vpy
  # Ask user for some information, using sensible defaults.
  eval "files=glob(input('Files [*.svg]? ') or '*.svg')"    # glob() creates a list of file based on a pattern
  eval "cols=int(input('Number of columns [3]? ') or 3)"
  eval "rows=ceil(len(files)/cols)"  # the number of rows depends on the number of files
  eval "col_width=convert_length(input('Column width [10cm]? ') or '10cm')"  # convert_length() converts string like '3cm' to pixels
  eval "row_height=convert_length(input('Row height [10cm]? ') or '10cm')"
  eval "margin=convert_length(input('Margin [0.5cm]? ') or '0.5cm')"
  eval "output_path=input('Output path [output.svg]? ') or 'output.svg'"

  # Create a grid with provided parameters.
  grid -o %col_width% %row_height% %cols% %rows%

      # Read the `_i`-th file. The last row may be incomplete so we use an empty path and `--no-fail`.
      read --no-fail "%files[_i] if _i < len(files) else ''%"

      # Layout the file in the cell.
      layout -m %margin% %col_width%x%row_height%
  end

  # wWrite the output file.
  write "%output_path%"

It can be used as follows::

  $ vpype -I grid.vpy
  Files [*.svg]?
  Number of columns [3]? 4
  Column width [10cm]?
  Row height [10cm]? 15cm
  Margin [0.5cm]?
  Output path [output.svg]?

The various parameters are queried and if nothing is provided as input, sensible defaults are used.


Processing recipes
===================

Optimizing a SVG for plotting
-----------------------------

This command will :ref:`cmd_read` a SVG file, merge any lines whose endings are less than 0.5mm from each other with :ref:`cmd_linemerge`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linemerge --tolerance 0.5mm write output.svg

In some cases such as densely connected meshes (e.g. a grid where made of touching square paths), :ref:`cmd_linemerge` may not be able to fully optimize the plot by itself. Using :ref:`cmd_splitall` before :ref:`cmd_linemerge` breaks geometries into their constituent segments and enables :ref:`cmd_linemerge` to perform a more aggressive optimization, at the cost of an increased processing time::

  $ vpype read input.svg splitall linemerge --tolerance 0.5mm write output.svg

This command will :ref:`cmd_read` a SVG file, simplify its geometry by reducing the number of segments in a line until they're a maximum of 0.1mm from each other using :ref:`cmd_linesimplify`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linesimplify --tolerance 0.1mm write output.svg

This command will :ref:`cmd_read` a SVG file, randomise the seam location for paths whose beginning and end points are a maximum of 0.03mm from each other with :ref:`cmd_reloop`, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg reloop --tolerance 0.03mm write output.svg

This command will :ref:`cmd_read` a SVG file, extend each line with a mirrored copy of itself three times using :ref:`cmd_multipass`, and then :ref:`cmd_write` a new SVG file. This is useful for pens that need a few passes to get a good result::

  $ vpype read input.svg multipass --count 3 write output.svg

This command will :ref:`cmd_read` a SVG file, use :ref:`cmd_linesort` to sort the lines to minimise pen-up travel distance, and then :ref:`cmd_write` a new SVG file::

  $ vpype read input.svg linesort write output.svg


Filtering out small lines
-------------------------

In some cases (for example when using Blender's freestyle renderer), SVG files can contain a lot of tiny lines which
significantly increase the plotting time and may be detrimental to the final look. These small lines can easily be
removed thanks to the :ref:`cmd_filter` command::

  $ vpype read input.svg filter --min-length 0.5mm write output.svg


HPGL export recipes
===================

Converting a SVG to HPGL
------------------------

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
--------------------------------------

If you are using the same type of plotter regularly, it may be cumbersome to systematically add the :option:`--device
<write --device>` option to the :ref:`cmd_write` command. The default device can be set in a configuration file (see
:ref:`faq_custom_config_file`) by adding the following section:

  .. code-block:: toml

    [command.write]
    default_hpgl_device = "hp7475a"


.. _faq_custom_hpgl_config:

Creating a custom configuration file for a HPGL plotter
-------------------------------------------------------

The configuration for a number of HPGL plotter is bundled with *vpype* (run ``vpype write --help`` for a list). If your
plotter is not included, it is possible to define your own plotter configuration in a custom configuration file
(see :ref:`faq_custom_config_file`).

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
  its X axis oriented along the long side and the Y axis oriented along the short side of the page.
* ``origin_location`` defines the physical location of (0, 0) plotter unit coordinate on the page, with respect to the
  top-left corner of the page in the orientation implied by ``paper_size``. In the example above, since the long edge
  is defined first, ``origin_location`` is defined based on the top-left corner in landscape orientation.
* ``y_axis_up`` defines the orientation of the plotter's native Y axis. Note that a value of ``true`` does **not** imply
  that ``origin_location`` is measured from the bottom-left corner, unless ``origin_location_reference`` is set to
  ``"botleft"``.


Using arbitrary paper size with HPGL output
-------------------------------------------

Some plotters such as the Calcomp Designmate support arbitrary paper sizes. Exporting HPGL with arbitrary paper size
requires a specific paper configuration. *vpype* ships with the ``flex`` and ``flexl`` configurations for the
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


Customizing *vpype*
===================

.. _faq_custom_config_file:

Creating a custom configuration file
------------------------------------

Some of *vpype*'s features (such as HPGL export) or plug-in (such as `vpype-gcode <https://github.com/plottertools/vpype-gcode>`_) can be customized using a configuration file using the `TOML <https://toml.io/en/>`_ format. The documentation of the features or plug-in using such a configuration file explains what it should contain. This section focuses on how a custom config file is made available to *vpype*.

The most common way is to create a `.vpype.toml` file at the root of your user directory, e.g.:

- ``C:\Users\username\.vpype.toml`` on Windows
- ``/Users/username/.vpype.toml`` on Mac
- ``/home/username/.vpype.toml`` on Linux

If such a file exists, it will be automatically loaded by *vpype* whenever it is used.

.. note::

   The ``.`` prefix in the file name will make the file **hidden** on most systems. This naming is typical for configuration files in the Unix world.


Alternatively, a configuration file may be provided upon invocation of *vpype* using the ``--confg`` option (or ``-c`` for short), e.g.::

  (vpype_venv) $ vpype --config my_config_file.toml [...]

Note that *vpype* does not "remember" the provided configuration file. The ``--config`` option must thus be provided on each invocation.

.. note::

   *vpype* is bundled with a `configuration file <https://github.com/abey79/vpype/blob/master/vpype/vpype_config.toml>`_. It is strongly discouraged to edit this file as it will be overwritten each time *vpype* is installed or updated.


.. _faq_custom_pen_config:

Creating a custom pen configuration
-----------------------------------

Pen configurations associate names, colors, and/or pen widths to specific layers and are applied by the :ref:`cmd_pens`
command. For example, the included ``cmyk`` pen configuration sets the name and color or layers 1 to 4 to cyan, magenta,
yellow, resp. black, while leaving pen widths unchanged. New pen configurations can be defined in a custom config file
(see :ref:`faq_custom_config_file`).

Pen configurations must conform to the following format to be valid:

  .. code-block:: toml

    [pen_config.my_pen_config]  # my_pen_config is this pen configuration's name
    layers = [
        # for each layer, a layer_id must be provided, but name, color and
        # pen_width are optional
        { layer_id = 1, name = "black layer", color = "black", pen_width = "0.15mm" },

        # any valid CSS color string and length unit may be used
        { layer_id = 2, name = "red layer", color = "#e00", pen_width = "0.05in" },

        # any attribute may be omitted, except layer_id
        { layer_id = 4, color = "#00de00" },

        # etc. (a pen configuration may have an arbitrary number of layers defined)
    ]

The above pen configuration can be used by referring to its name, in this case ``my_pen_config``::

  $ vpype [...] pens my_pen_config [...]


Miscellaneous recipes
=====================

.. _faq_interactive_pipelines:

Create interactive scripts with ``input()``
-------------------------------------------

The Python :func:`input` function is available in :ref:`expressions <fundamentals_expression_substitution>`. It can be used to interactively query the use for parameter values. For example, this pipeline asks the user for a margin value and uses it to layout a SVG::

  $ vpype \
      eval "margin = float(input('Margin in cm? '))" \
      read input.svg \
      layout --fit-to-margin %margin*cm% a4 \
      write output.svg
  Margin in cm? 3

This pattern can be improved by providing a default value, allowing the user to simply type <Enter> to use it::

  $ vpype \
      eval "margin = float(input('Margin in cm [3cm]? ') or 3)" \
      ...

This works because of the particular way in which the ``or`` operator behaves. It evaluates to the first operand whose truthiness is :data:`True`. When the user directly hits <Enter>, the first operand is an empty string, whose truthiness is :data:`False`. The ``or`` expression thus evaluates to the second operand in this case.

See :ref:`faq_merge_to_grid` for a real-world example that makes use of this pattern.

Batch processing many SVG with bash scripts and ``parallel``
------------------------------------------------------------

Computers offer endless avenues for automation, which depend on OS and the type of task at hand. Here is one way to
easily process a large number of SVG with the same *vpype* pipeline. This approach relies on the
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


External scripts
----------------

The :ref:`cmd_script` command is a very useful generator that relies on an external Python script to produce geometries. Its
use is demonstrated by the `alien.sh` and `alien2.sh` examples. A path to a Python file must be passed as argument.
The file must implement a `generate()` function which returns a Shapely `MultiLineString` object. This is very easy
and explained in the `Shapely documentation <https://shapely.readthedocs.io/en/latest/manual.html#collections-of-lines>`__.



..
  This are example of how to refer to commands, sections, etc.:

  See :ref:`cmd_write` command.

  The :ref:`fundamentals_blocks` section.

  The :py:class:`LineCollection` class.

  The :option:`--single-path <write --single-path>` option.

  The :doc:`plugins` pages.
