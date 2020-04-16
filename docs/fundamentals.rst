============
Fundamentals
============

A pipeline of lines
-------------------

Useful output is obtained from *vpype* by composing 'pipelines' of 'commands'. In a given pipeline, geometries are passed from command to command, starting with the first all the way to the last.

.. image:: images/pipeline.svg

Pipelines are created by passing *vpype* with the first command name together with its options and arguments, then the next command name, etc.::

  $ vpype command1 [--option X [...]] [ARG [...]] command2 [--option X [...]] [ARG [...]] ...

The list of every commands is available in from the CLI::

  $ vpype --help
  Usage: vpype [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Options:
    -v, --verbose
    -I, --include PATH  Load commands from a command file.
    -H, --history       Record this command in a `vpype_history.txt` in the
                        current directory.
    -s, --seed INTEGER  Specify the RNG seed.
    --help              Show this message and exit.

  Commands:

    Primitives:
      circle        Generate lines approximating a circle.
      line          Generate a single line.
      rect          Generate a rectangle.

    Operations:
      crop          Crop the geometries.
      linemerge     Merge lines whose endings overlap or are very close.
      ...

Help on each command is also available on the CLI, for example::

  $ vpype circle --help
  Usage: vpype circle [OPTIONS] X Y R

    Generate lines approximating a circle.

    The circle is centered on (X, Y) and has a radius of R.

  Options:
    -q, --quantization LENGTH  Maximum length of segments approximating the
                               circle.
    -l, --layer LAYER          Target layer or 'new'.
    --help                     Show this message and exit.


Geometries made of layers
-------------------------

The geometries passed from command to command is organised as a collection of layers, each containing a collection of paths.

.. image:: images/layers.svg
   :width: 300px

Each layer contains an ordered collection of paths. Paths are described by a sequence of 2D points connected by line segment. *vpype* does not support curved path. Instead, everything is linearised into small segments. In particular, the :program:`read` command transform all curved SVG elements (such as circle or bezier paths) into sequence of segments with a quantization that can be defined by the user. This makes *vpype* very flexible and, provided that the quantization is kept low enough, has no impact on the final, plotted result, but is one of the reason why *vpype* cannot be (and is not meant as) a general-purpose vector data processing tool.

In *vpype*, layers are identified by a non-zero positive integer.


A taxonomy of command
---------------------

Commands come in 3 different types: *generators*, *layer processors* and *global processors*. Although not strictly necessary to use *vpype*, understanding the difference between them help to have a good grasp on how it works, and is necessary if you plan on writing your own plug-in.

.. image:: images/command_types.svg
   :width: 600px


Generators
^^^^^^^^^^

Generators add new geometries to a target layer, ignoring (but preserving) any content in this layer. Other layers' content is not affected by a generator. They accept a ``--layer TARGET`` option to control which layer should receive the new geometries. By default, the target layer of the previous generator command is used, or layer 1 if the generator is the first. Here is an example::

  $ vpype line --layer 3 0 0 1cm 1cm circle 0.5cm 0.5cm 0.5cm

Both :program:`line` and :program:`circle` are generator commands which both create the type of paths you would expect. In this case, both the circle and the line end up in layer 3. For generators, ``--layer new`` can also be used to generate geometries in the empty layer with the lowest possible identifier.

Here are a few more example of generators (the list is not exhaustive):
- :program:`read`: reads geometries from a SVG file
- :program:`rect`: generates a rectangle
- :program:`frame`: generates a single-line frame around the existing geometries


Layer processors
^^^^^^^^^^^^^^^^

Contrary to generators, layer processors generally do not produce new paths but instead modify existing geometries. Further, they do so on a layer by layer basis. This means that the way a layer processor modifies one layer's content bears no consequences on how it will affect another layer. Let's consider for example :program:`linemerge`. This command looks for paths whose either endings are close to each other (according to some tolerance) and merges them when they are, avoiding costly pen-up/pen-down operations by the plotter. Since :program:`linemerge` is a layer processor, it will only merge paths within the same layer.

Layer processors accept a ``--layer TARGET[,TARGET[,...]]`` option to specify one or more layer on which they should be applies. Here are some examples::

  $ vpype [...] crop --layer 1      0 0 10cm 10cm
  $ vpype [...] crop --layer 1,2,4  0 0 10cm 10cm
  $ vpype [...] crop --layer all    0 0 10cm 10cm

All these commands do exactly what you think they should do. If the ``--layer`` option is omitted, then ``all`` is assumed and layer processors will process every single (existing) layer. Note that if you provide a list of layers, they must be comma separated and without any whitespace.

Here are a few examples of layer processors (the list is non-exhaustive):
- :program:`translate`: apply a translation on the geometries
- :program:`linesort`: sort paths within the layer such as to minimize the distance travelled by the plotter in pen-up position
- :program:`linesimplify`: reduce the number of points in paths which ensuring a specified precision, in order to minimize output file size


Global processors
^^^^^^^^^^^^^^^^^

While layer processors are executed multiple times, once for each layer they are applied on, global processors are executed only once and may have a global effect of all layers.

.. TODO to be completed


Here are a few examples of layer processors (the list is non-exhaustive):
- :program:`translate`, :program:`rotate`, :program:`scale`, :program:`skew`: transformation commands that do exactly what their name suggest


Units
-----

Being designed for plotter data, all _vpype_ understands is lines. Specifically, straight lines. This makes _vpype_ a
very poor general purpose vector graphics tool, but hopefully a good one when dealing with graphics files sent to
plotters. When loading geometries from existing SVG file (using the `read` command), curved paths such as Bezier
curves or ellipses are converted into multiple, typically small segments. The quantization interval is 1mm by default,
but can be changed with the `--quantization` option of the `read` command.

Internally, _vpype_ use the CSS pixel as unit, which is defined as 1/96th of an inch, which happens to be the default
unit used by the SVG format. Most commands understand other standard units thought, including `in`, `cm`, `mm`, `pt` and
`pc`. These two commands thus generate the same output (100 random lines in a 1x1in square in the middle of an A4 page)::

  $ vpype random --count 100 --area 96 96 write --page-format a4 --center output.svg
  $ vpype random --count 100 --area 1in 1in write --page-format a4 --center output.svg


Blocks
------

Blocks refer to a portion of the pipeline marked by the `begin` and `end` special commands.
The command immediately following `begin` is called the _block processor_ and defines how many times this portion of
the pipeline will be used. For example, the `grid` block layer_processor repeatedly execute the block and arranges the
resulting geometries on a regular NxM grid. This is how the top banner has been generated::

  vpype begin \
    grid --offset 1.5cm 1.5cm 13 20 \
    script alien_letter.py \
    scale --to 0.8cm 0.8cm \
  end \
  write --page-format a3 --center alien.svg

The pipelines above mainly consist of a block with the `grid` block layer_processor. It is repeated on the 13 by 20 grid, with
a spacing of 1.5cm in both direction. On each of these location, the script `alien_letter.py` is executed to generate
some geometries, which are then scaled to a 0.8x0.8cm size. After the block, we `write` the result to a SVG.

Notice how, with added newlines and proper indenting, the sequence of commands emerges as a kind of mini-language. You
guessed it, blocks can be nested to achieve more complex compositions. Here is an example::

  vpype begin \
    grid --offset 8cm 8cm 2 3 \
      begin \
        grid --offset 2cm 2cm 3 3 \
        random --count 20 --area 1cm 1cm \
        frame \
      end \
    frame --offset 0.3cm \
  end \
  show

This pipeline should display the following:

<img src="https://i.imgur.com/eWCUuII.png" alt="blocks of random lines" width=300>


Command file
------------

When pipelines become complex, the number of command-line arguments can become too large to be convenient. To address
this, `vpype` support the inclusion of command files in the pipeline. A command file is a text file whose content is
interpreted as if it was command-line arguments.

The previous example can be converted to a command file with the following content::

  # this is an example command file
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


The command file can then be loaded as argument using the `-I` or `--include` option::

  $ vpype -I command_file.vpy

Newlines and indentation are ignored and useful only for readability. Everything right of a `#` character is considered
a comment and thus ignored. Command files can be mixed with regular arguments too::


  $ vpype -I generate_lines.vpy write -p a4 -c output.svg

Finally, command files can also include other command files::

  # Example command file
  begin
    grid --offset 1cm 1cm 2 2
    -I sub_command.vpy
  end
  show



Plug-ins
--------

_vpype_ support plug-ins to extend its capabilities. Here are a few known plug-ins.

### [vpype-text](https://github.com/abey79/vpype-text): generate plottable text with Hershey fonts (based on [axi](https://github.com/fogleman/axi))

### [vpype-pixelart](https://github.com/abey79/vpype-pixelart): easy pixel art plotting

<img src="https://i.redd.it/g1nv7tf20aw11.png" alt="pixel art by u/_NoMansDream" width=400 />
<img src="https://i.imgur.com/dAPqFGV.jpg" alt="line mode plotted pixelart" width=400 />

(original art by Reddit user [u/\_NoMansDream](https://www.reddit.com/user/_NoMansDream/))

### [hatched](https://github.com/abey79/hatched): convert images to hatched patterns

<img src="https://i.imgur.com/QLlBpNU.png" width=300 /> <img src="https://i.imgur.com/fRIrPV2.jpg" width=300 />

Creating custom plug-ins is very easy. It's a great way to implement your next plotter art project as you directly
benefit from all of _vpype_'s features (export to SVG, line order optimisation, etc.). Check the
[plug-in documentation](plugins) for more information on how to develop your own plug-in.



