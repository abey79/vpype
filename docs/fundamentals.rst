============
Fundamentals
============

.. highlight:: bash

.. _fundamentals_pipeline:

Pipeline
========

To use *vpype*, you compose 'pipelines' of 'commands'. In a given pipeline, geometries are passed from command to command, starting with the first all the way to the last.

.. image:: images/pipeline.svg

Pipelines are created by passing *vpype* the first command name together with its options and arguments, then the next command name, and so on.::

  $ vpype command1 [--option X [...]] [ARG [...]] command2 [--option X [...]] [ARG [...]] ...

The list of every command is available by running the help option on the core vpype command::

  $ vpype --help
  Usage: vpype [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Options:
    -v, --verbose
    -I, --include PATH  Load commands from a command file.
    -H, --history       Record this command in a `vpype_history.txt` in the
                        current directory.
    -s, --seed INTEGER  Specify the RNG seed.
    --help              Show this message and exit.
      ...

Help on each command is also available by running the help option on that command, for example::

  $ vpype circle --help
  Usage: vpype circle [OPTIONS] X Y R

    Generate lines approximating a circle.

    The circle is centered on (X, Y) and has a radius of R.

  Options:
    -q, --quantization LENGTH  Maximum length of segments approximating the
                               circle.
    -l, --layer LAYER          Target layer or 'new'.
    --help                     Show this message and exit.


.. _fundamentals_lines_layers:

Lines and layers
================

The geometries passed from command to command are organised as a collection of layers, each containing a collection of paths.

.. image:: images/layers.svg
   :width: 300px

The primary purpose of layers in *vpype* is to create or process files for multicolored plots, where each layer contains geometries to be drawn with a specific pen or color. In *vpype*, layers are identified by a non-zero, positive integer (e.g. 1, 2,...). You can have as many layers as you want, memory permitting.

Each layer consists of an ordered collection of paths. In *vpype*, paths are so-called "polylines", meaning lines made of one or more straight segments. Each path is therefore described by a sequence of 2D points. Internally, these points are stored as complex numbers (this is invisible to the user but relevant to :ref:`plugin <plugins>` writers).

Curved paths are not supported *per se*. Instead, curves are converted into linear segments that are small enough to approximate curvature in a way that is invisible in the final plot. For example, the :program:`read` command transforms all curved SVG elements (such as circles or bezier paths) into paths made of segments, using a maximum segment size that can be set by the user (so-called "quantization"). This design choice makes *vpype* very flexible and easy to develop, with no practical impact on final plot quality, but is the primary reason why *vpype* is not fit to be (and is not meant as) a general-purpose vector data processing tool.

One downside of using polylines to approximate curved element is a potential increase in output file size. For example, three numbers are sufficient to describe a circle, but 10 to 100 segments may be needed to approximate it sufficiently well for plotting. When this becomes an issue, tuning the quantization parameters with the ``-q`` option or using the :program:`linesimplify` command can help.


.. _fundamentals_commands:

Command taxonomy
================

Commands come in three different types: *generators*, *layer processors* and *global processors*. Although it is not strictly necessary to understand the difference between them to use *vpype*, it helps to have a good grasp on how they work, and is very useful if you plan on writing your own :ref:`plug-ins <plugins>`.

.. image:: images/command_types.svg
   :width: 600px


.. _fundamentals_generators:

Generators
----------

Generators add new geometries to a target layer, ignoring (but preserving) any content already existing in the layer. Other layers' content is not affected. They accept a ``--layer TARGET`` option to control which layer should receive the new geometries. By default, the target layer of the previous generator command is used, or layer 1 if the generator is the first. Here's an example::

  $ vpype line --layer 3 0 0 1cm 1cm circle 0.5cm 0.5cm 0.3cm

This command will first draw a :program:`line` on layer 3 from the point (0,0) a point at (1cm, 1cm), then it will draw a :program:`circle` also on layer 3 (defaulting to the target of the previous command) centred on the point (0.5cm, 0.5cm), with a radius of 0.3cm.

For generators, ``--layer new`` can be used to generate geometries in a new, empty layer with the lowest possible number identifier.

A few more examples of generators include:

* :program:`rect`: generates a rectangle
* :program:`arc`: generates lines approximating a circular arc
* :program:`frame`: generates a single-line frame around the existing geometries


.. _fundamentals_layer_processors:

Layer processors
----------------

Unlike generators, layer processors generally don't produce new paths but instead modify existing ones on a layer-by-layer basis. This means that the way a layer processor changes one layer's content has no bearing on how it will affect another layer. Let's consider for example :program:`linemerge`. This command looks for paths whose ends are close to one another (according to some tolerance) and merges them to avoid unnecessary pen-up/pen-down operations by the plotter. Since :program:`linemerge` is a layer processor, it will only merge paths within the same layer.

Layer processors accept a ``--layer TARGET[,TARGET[,...]]`` option to specify one or more layer on which they should be applied. Here are some examples::

  $ vpype [...] crop --layer 1      0 0 10cm 10cm
  $ vpype [...] crop --layer 1,2,4  0 0 10cm 10cm
  $ vpype [...] crop --layer all    0 0 10cm 10cm

All these commands crop the specified layers to a 10cm x 10cm rectangle with a top-left corner at (0,0). If the ``--layer`` option is omitted, then ``all`` is assumed and the layer process will target every single (existing) layer. Note that if you provide a list of layers, they must be comma separated without any whitespace.

A few more examples of layer processors include:

* :program:`translate`: apply a translation to the geometries (i.e. move them)
* :program:`linesort`: sort paths within the layer in such a way that the distance travelled by the plotter in pen-up position is minimized
* :program:`linesimplify`: reduce the number of points in paths while ensuring a specified precision, in order to minimize output file size


.. _fundamentals_global_processors:

Global processors
-----------------

While layer processors are executed multiple times, once for each layer they are targeted to, global processors are executed only once and apply to all layers. Depending on the command, they may or may not have layer-related parameters, although there is no rule about that.

For example, the :program:`write` command uses all layers in the pipeline to generate a multi-layer SVG file. The :program:`rotate`, :program:`scale`, and :program:`skew` transformation commands are also implemented as global processors because they use the center of the geometry as reference (by default), although they also accept a `--layer` option which makes them behave much like a layer processor.

.. _fundamentals_units:

Units
=====

Like the SVG format, the default unit used by *vpype* is the CSS pixel, which is defined as 1/96th of an inch. For example, the following command will generate a 1-inch-radius circle centered on coordinates (0, 0)::

  $ vpype circle 0 0 96

Because the pixel is not the best unit to use with physical media, most commands understand other CSS units including ``in``, ``cm``, ``mm``, ``pt`` and ``pc``. The 1-inch-radius circle can therefore also be generated like this::

  $ vpype circle 0 0 1in

Note that there must be no whitespace between the number and the unit, otherwise they would be considered as different command-line arguments.

Internally, units other than CSS pixels are converted as soon as possible and pixels are used everywhere in the code (see :class:`Length`).


.. _fundamentals_blocks:

Blocks
======

.. image:: images/block.svg
   :width: 600px

Blocks refer to a portion of the pipeline marked by the :program:`begin` and :program:`end` special commands. The command immediately following :program:`begin` is called the *block processor* and controls how many times the block pipeline is executed and what is done with the geometries it produced.

A commonly used block processor is the :program:`grid` command. It repeatedly executes the commands inside the block (known as the "block pipeline") and arranges the results on a regular grid. For example, this command generates a grid of five by ten 0.5-inch-radius circles, with a spacing of two inches in both directions::

  $ vpype begin                     \
        grid --offset 2in 2in 5 10  \
        circle 0 0 0.5in            \
      end                           \
      show

Note: The backslashes allow you to escape the end-of-line and split a command across multiple lines. In this case, it highlights the nested structure of blocks and how it emerges as some kind of mini-language.

Here is the result:

.. image:: images/circle_grid.png
   :width: 400px

Let's break down what's happening here. The :program:`begin` and :program:`end` define a block whose processor is the :program:`grid` command. The block pipeline consists of a single :program:`circle` command, which generates a 0.5-inch-radius circle centered on 0, 0. The pipeline is executed 50 times (once for every location in a 5x10 grid), and the result is translated (i.e. moved) two inches each time by the :program:`grid` command. After the block, the :program:`show` commands displays the result.

Blocks can be nested to achieve more complex compositions. Here is an example::

  $ vpype begin                           \
    grid --offset 8cm 8cm 2 3             \
      begin                               \
        grid --offset 2cm 2cm 3 3         \
        random --count 20 --area 1cm 1cm  \
        frame                             \
      end                                 \
    frame --offset 0.3cm                  \
  end                                     \
  show

And the result:

.. image:: images/random_grid.png
   :width: 400px

When using blocks, it is important to understand that a block pipeline is always executed from a blank state, even if geometries exist before the block begins. The block pipeline's result is added to the global (or parent) pipeline only at the end of the block. To understand this, consider the following example (the :program:`ldelete` command deletes the layer passed in argument)::

  $ vpype                           \
      circle --layer 1 0 0 1cm      \
      begin                         \
        grid --offset 2cm 2cm 3 3   \
        ldelete 1                   \
        circle --layer 10 0 0.5cm   \
      end                           \
      show

Before the block, a 1cm-radius circle is added to layer 1. Then, the block pipeline starts by initializing a 3x3 grid - for each space in the grid it deletes layer 1 before adding a 0.5cm-radius circle. However, since the block pipeline is executed from a blank state, the :program:`ldelete` command has nothing to remove and all 10 circle (nine from the grid block on layer 10, plus the original on layer one) are visible in the output:

.. image:: images/ldelete_grid.png
   :width: 400px

.. _fundamentals_command_files:

Command files
=============

Pipelines be quite complex, especially when using blocks, which can become cumbersome to include in the command-line. To address this, all or parts of a pipeline of commands can be stored in so-called "command files" which *vpype* can then refer to. A command file is a text file whose content is interpreted as if it was command-line arguments. Newlines and indentation are ignored and useful only for readability. Everything to the right of a ``#`` character is considered
a comment and is ignored.

The nested block example from the previous section could be converted to a command file with the following content::

  # command_file.vpy - example command file
  begin
    grid --offset 8cm 8cm 2 3
      begin
        grid --offset 2cm 2cm 3 3
        random --count 20 --area 1cm 1cm
        frame
      end
    frame --offset 0.3cm
  end
  show

The command file can then be loaded as an argument using the `-I` or `--include` option::

  $ vpype -I command_file.vpy

Regular arguments and command files can be mixed in any combination::

  $ vpype -I generate_lines.vpy write -p a4 -c output.svg

Finally, command files can also reference other command files::

  # Example command file
  begin
    grid --offset 1cm 1cm 2 2
    -I sub_command.vpy
  end
  show

