<img src="https://i.imgur.com/LM2Qrc0.png" alt="banner" width=1200>


# _vpype_ ![Test](https://github.com/abey79/vpype/workflows/Test/badge.svg?branch=master) [![Documentation Status](https://readthedocs.org/projects/vpype/badge/?version=latest)](https://vpype.readthedocs.io/en/latest/?badge=latest)


> **Note**: a proper documentation is [under construction](https://vpype.readthedocs.io/en/latest/).

_vpype_ aims to be the one-stop-shop, Swiss Army knife<sup>1</sup> for producing plotter-ready vector graphics. Here
are, for illustration, a few examples of what it can do:

- Load an SVG file, scale it to a specific size, and export it centered on an A4-sized, ready-to-plot SVG file.
    ```bash
    $ vpype read input.svg scale --to 10cm 10cm write --page-format a4 --center output.svg
    ```
- Visualize the path structure of large SVG files, showing whether lines are properly joined or
    not thanks to a colorful display.
    ```bash
    $ vpype read input.svg show --colorful
    ```
- Optimize paths to reduce plotting time (merge connected lines and sort them to minimize pen-up distance):
    ```bash
    $ vpype read input.svg linemerge --tolerance 0.1mm linesort write output.svg
    ```
- Load several SVG files and save them as a single, multi-layer SVG file (e.g. for multicolored drawings).
    ```bash
    $ vpype read -l 1 input1.svg read -l 2 input2.svg write output.svg
    ```
- Create arbitrarily-sized, grid-like designs like this page's top banner.
    ```bash
    $ vpype begin grid -o 1cm 1cm 10 13 script alien_letter.py scaleto 0.5cm 0.5cm end show
    ```
- Export to HPGL for vintage plotters.
    ```bash
    $ vpype read input.svg write --device hp7475a --page-format a4 --landscape --center output.hpgl
    ```

At its core, _vpype_ allows the user to build pipelines of _commands_, each of which receives a
collection of vector graphics (basically, lines), modifies them and/or produce new ones, and passes them to the next
command. _vpype_'s simple CLI user interface makes it a breeze to create these pipelines, which can be expanded thanks
to a [plug-in](PLUGINS.md) architecture.

Let's take a closer look at an example:

```bash
$ vpype random --count 100 --area 10cm 10cm rotate 45 write --page-format a4 --center output.svg
```

This pipelines uses 3 commands (`random`, `rotate` and `write`) to generate 100 random lines in a 10x10cm square,
rotate them by 45 degrees, and save them in the middle of an A4-sized SVG file. This is how the output would look in
InkScape:

<img src="https://i.imgur.com/d9fSrRh.png" alt="100 random lines in a 10x10cm box rotated by 45 degrees" width=300>

Because _vpype_ focuses only on vector graphics for use as input for pen plotters, its data model is very simple and only includes
paths (without formatting options like line color, width, etc.), filled shapes, bitmaps, etc. This is the core of what
makes _vpype_ both simple and powerful at what it does.  

This project is young and being actively developed. Your feedback is important!

_vpype_ is written in Python and relies on
[Click](https://palletsprojects.com/p/click/),
[Shapely](https://shapely.readthedocs.io),
[rtree](http://toblerity.org/rtree/),
[svgwrite](https://svgwrite.readthedocs.io),
[svgpathtools](https://github.com/mathandy/svgpathtools),
[matplotlib](https://matplotlib.org),
and [NumPy](https://numpy.org).
Additionally, there are many other projects which have helped get _vpype_ where it is today.

<sup>1</sup>Although not in the military the author is indeed Swiss :) 🇨🇭


## Getting Started

### Installation

See [installation instructions](INSTALL.md).


### Running example scripts

A few examples of the scripting functionality are available in the `examples` folder, in the form of bash scripts. The script used to create
the top banner is included:

```bash
$ cd examples
$ ./alien.sh
```


### Documentation

The CLI user interface documentation is available in the shell. Use `vpype --help` to see a list of
all available commands, including installed plugins:

```text
$ vpype --help
Usage: vpype [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

Options:
  -v, --verbose
  -I, --include PATH  Load commands from a command file.
  --help              Show this message and exit.

Commands:

  [...]

  Input:
    read       Extract geometries from a SVG file.
    script     Call an external python script to generate geometries.

  Transforms:
    rotate     Rotate the geometries.
    scale      Scale the geometries.
    skew       Skew the geometries.
    translate  Translate the geometries.

  [...]
```

Use `vpype COMMAND --help` for information on a specific command, for example:

```text
$ vpype scale --help
Usage: vpype scale [OPTIONS] SCALE...

  Scale the geometries by a factor.

  The origin used is the bounding box center, unless the `--origin` option
  is used.

  By default, act on all layers. If one or more layer IDs are provided with
  the `--layer` option, only these layers will be affected. In this case,
  the bounding box is that of the listed layers.

  Example:

      Double the size of the geometries in layer 1, using (0, 0) as origin:

          vpype [...] scale -l 1 -o 0 0 2 2 [...]

Options:
  -l, --layer LAYERS      Target layer(s).
  -o, --origin LENGTH...  Use a specific origin.
  --help                  Show this message and exit.
```


### Generator-filter-sink theory

_vpype_ commands can be broadly categorized in one of three groups, based on what they do:

- _Generators_ create new geometries (e.g. read data in from an SVG file, generate random lines, etc.).
- _Filters_ alter the existing geometries (e.g. translate, rotate, etc.).
- _Sinks_ use the existing geometries to display or export _without_ modifying them.

Typically in this data theory, generators will be at the beginning of pipelines, filters in the middle, and sinks at the end.
_vpype_ does not strictly enforce, nor internally require this theory, but it helps the user to plan pipelines. A command could both modify existing geometries and
add new ones, and sinks don't actually "eat" geometries as the name may imply. Geometries are instead passed on, which
enables multiple sinks to be chained (e.g. first display the result, then save it to SVG).

consider the following example:
```
    group: [generator]->[ filter ]->[ sink  ]->[  filter  ]->[    sink    ]->[         generate AND filter         ]->[ sink  ]
functions: [read svg] ->[scale 2x]->[display]->[rotate 45˚]->[write to svg]->[replicate geometry, rotating randomly]->[display]
```
Here is a non-exhaustive list of important commands:

- `read`: import geometries from a SVG file
- `line`, `rect`, `arc`, `circle`: create the corresponding primitives
- `script`: execute a Python script to generate geometries (see [External scripts](#external-scripts))
- `translate`, `rotate`, `scale`, `skew`: basic transformation commands which do exactly what you think they do
- `crop`: crop the geometries, removing everything outside of a rectangular area
- `linemerge`: merge lines whose endings overlap or are very close
- `linesort`: sort lines to minimize the total distance between the end of a path to the start of the next one
- `multipass`: prepare two-pass (or more) files for when a single stroke isn't sufficient for a good render
- `frame`: add a simple frame around the geometries
- `lmove`, `lcopy`, `ldelete`: layer manipulation commands
- `show`: display the geometries in a `matplotlib` window
- `write`: save the geometries as an SVG or HPGL file


### Data model and units

Being designed for plotter data, _vpype_ only understands lines, specifically straight lines. This makes _vpype_ a
very poor general purpose vector graphics tool, but hopefully a good one when dealing with graphics files intended for pen
plotters. When loading geometries from an existing SVG file (using the `read` command), curved paths such as Bezier
curves or ellipses are converted into multiple, typically small, straight segments. The curve quantization interval is 1mm by default,
but can be changed with the `--quantization` option of the `read` command.

Internally, _vpype_ uses the CSS pixel as its default unit, which is defined as 1/96th of an inch. This also happens to be the default
unit used by the SVG format. Most commands understand other standard units though, including `in`, `cm`, `mm`, `pt` and
`pc`. Thus, these two commands will generate the same output (100 random lines in a 1x1in square in the middle of an A4 page):

```bash
$ vpype random --count 100 --area 96 96 write --page-format a4 --center output.svg
$ vpype random --count 100 --area 1in 1in write --page-format a4 --center output.svg
```


### Layers

_vpype_ supports multiple layers and can produce multi-layer SVGs, which can be useful for multicolored drawings.
Most commands have a `-l, --layer` option which affects how layers are created and/or modified.
Layers are always referred to by a non-zero, positive integer (which aligns nicely with how official
[AxiDraw](https://axidraw.com) tools deal with layers).

Generators such as `line`, `script`, etc. which create new geometries use `--layer` to specify which layer receives
these new geometries. By default, the last target layer is used:
```
$ vpype line --layer 3 0 0 1cm 1cm circle 0.5cm 0.5cm 0.5cm show
```
Here, both the line and the circle will be in layer 3. If no generator specifies a target layer, then layer 1 is used
by default.

The `read` command honors the input SVG file's layer structure and will create _vpype_ layers for each layer in the SVG file (i.e. for each top-level SVG group, see the CLI help
for further details). Alternatively, `read` can be run in single-layer mode by adding the `--single-layer` argument. In this case, all geometries are
loaded in one layer, regardless of the SVG file's structure.

Filters such as `translate`, `rotate`, `crop`, `linemerge`,  etc. which modify existing geometries use `--layer` to
control if one, several or all layers will be affected:
```
$ vpype [...] rotate --layer 1 [...]
$ vpype [...] rotate --layer 1,2,4 [...]
$ vpype [...] rotate --layer all [...]
```
All these commands do exactly what you think they should do. If the `--layer` option is omitted, then `all` is assumed.
Note that if you provide a list of layers, they must be comma separated and _without_ any whitespace, as the list must be
a single CLI argument.

Some commands do not have a `--layer` option, but do understand the layer data. For example, `show` will display each layer
in a different color by default. Last but not least, `write` will generate multi-layer SVG files which will work as expected
in InkScape without further modification.

Finally, layers' content can be moved or copied to other layers with the `lmove` and `lcopy` commands, and
deleted with the `ldelete` command. See these commands' help for details.


### External scripts

The `script` command is a very useful generator that relies on an external Python script to produce geometries. Its
use is demonstrated by the `alien.sh` and `alien2.sh` examples. A path to a Python file must be passed as argument.
The file must implement a `generate()` function which returns a Shapely `MultiLineString` object. Creating this is very easy,
and is explained in the [Shapely documentation](https://shapely.readthedocs.io/en/latest/manual.html#collections-of-lines).

`script` is distinct from plugins in the ways they interface with _vpype_ data pipelines. Plugins have more direct access, but are expected to
function in the generator-filter-sink theory. This means they must be more well-behaved with how they treat incoming and outgoing data,
but are able to more easily access geometry from other generators without needing intermediary sinks (e.g. SVG file writes).
`script`s on the other hand, can be a lot looser with their geometry handling, and have the ability to incorporate other, less related features,
because they are more free-form scripts.


### Blocks

Blocks refer to a prepared portion of pipeline marked by the special commands `begin` and `end`.
The command immediately following `begin` is called a _block processor_ and defines (directly or implicitly) how many times this portion of
the pipeline will be used. For example, the `grid` block processor repeatedly executes the block and arranges the
resulting geometries on a regular NxM grid. This is how the top banner was generated:

```bash
vpype begin \
  grid --offset 1.5cm 1.5cm 13 20 \
  script alien_letter.py \
  scale --to 0.8cm 0.8cm \
end \
write --page-format a3 --center alien.svg
```

The pipeline above mainly consists of a block with the `grid` block processor. On each intersection of a 13 by 20 grid, with
a spacing of 1.5cm in both directions, it executes the script `alien_letter.py` to generate
some geometries, which are then scaled to a 0.8x0.8cm size. After the block, we `write` the result to an SVG file.

Notice how, with added newlines and proper indenting, the sequence of commands emerges as a kind of pseudo-language. You
guessed it, blocks can be nested to achieve more complex compositions. Here is an example:

```bash
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
```

This pipeline should display the following:

<img src="https://i.imgur.com/eWCUuII.png" alt="blocks of random lines" width=300>


### Command file

As pipelines become more complex, the number of command-line arguments needed can become too large to type into the shell easily. To address
this, `vpype` supports the inclusion of command files in the pipeline. A command file for _vpype_ is a text file whose content is
interpreted as if it were a series of command-line arguments.

The previous nested grid example can be converted to a command file like so:
```bash
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
```

The command file can then be loaded as an argument using the `-I` or `--include` option:

```bash
$ vpype -I command_file.vpy
```

Newlines and indentation are ignored and only used for human readability. Comments can be written in Python style, i.e. `#like this comment`
Command files can be mixed with regular arguments too:

```text
$ vpype -I generate_lines.vpy write -p a4 -c output.svg
```

Finally, command files can also include other command files:

```text
# Example command file
begin
  grid --offset 1cm 1cm 2 2
  --include sub_command.vpy
end
show
```


### Plug-ins

_vpype_ supports plug-ins to extend its capabilities. Here is a (non-exhaustive) list of plug-ins.

#### [vpype-text](https://github.com/abey79/vpype-text): generate plottable text with Hershey fonts (based on [axi](https://github.com/fogleman/axi))

#### [vpype-pixelart](https://github.com/abey79/vpype-pixelart): easy pixel art plotting

<img src="https://i.redd.it/g1nv7tf20aw11.png" alt="pixel art by u/_NoMansDream" width=400 />
<img src="https://i.imgur.com/dAPqFGV.jpg" alt="line mode plotted pixelart" width=400 />

(original art by Reddit user [u/\_NoMansDream](https://www.reddit.com/user/_NoMansDream/))

#### [hatched](https://github.com/abey79/hatched): convert images to hatched patterns

<img src="https://i.imgur.com/QLlBpNU.png" width=300 /> <img src="https://i.imgur.com/fRIrPV2.jpg" width=300 />

Creating custom plug-ins is very easy. It's a great way to implement your next plotter art project as you directly
benefit from all of _vpype_'s features (exporting to SVG, line order optimization, etc.). Check the
[plug-in documentation](PLUGINS.md) for more information on how to develop your own plug-in.


## Contributing

This project is at an early (but fully functional) stage and welcomes all types of contributions. The most important way to contribute is by
[filing Issues](https://github.com/abey79/vpype/issues) describing bugs you are experiencing or features you would
like to see added. Understanding your use-case and workflow is key for _vpype_ to evolve in the right direction.

Code contributions are, of course, very welcome. Feel free to also open [pull
requests](https://github.com/abey79/vpype/pulls) to contribute actual code. Note that this project uses
[`black`](https://github.com/psf/black) for code formatting to create a uniform style.


### Development environment

The first step in setting up the dev environment cleanly is to download the code:

```bash
$ git clone https://github.com/abey79/vpype.git
```

Then, create a virtual environment, update pip and install development dependencies:

```bash
$ cd vpype
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
```

Finally, install your copy of _vpype_ as an editable package:

```
$ pip install -e .
```

The `vpype` executable will then be available in the terminal and be based on the locally stored source code (including your edits).
If you are using an IDE, point its run/debug configuration to `venv/bin/bin/vpype`.


### Running the CI tests

You can run tests with the following command:

```bash
$ pytest
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
