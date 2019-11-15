<img src="https://i.imgur.com/LM2Qrc0.png" alt="banner" width=1200>

# _vpype_

_vpype_ is a tool to create and process vector graphics for pen plotters by means of easy-to-build CLI
pipelines (pen plotters, such as the [AxiDraw](https://axidraw.com), are robotic drawing machines).
It can achieve simple tasks like scaling a SVG to a defined physical size and centering it on an
A4 page (to make a ready-to-plot file) to more complex task like compositing the output of multiple scripts into
full-blow art pieces.

At its core, _vpype_ allows the user to build pipelines of processing units, or _commands_, each of which receives a
collection of vector graphics (basically, lines), modifies them and/or produce new ones, and pass them to the next
command. _vpype_ provides a nice CLI user interface to create these pipelines. For example, this pipelines uses
3 commands (`random`, `rotate` and `write`) to generates 100 random lines in a 10x10cm square, rotate them by 45
 degrees, and saves them in the middle of an A4 SVG file:

```bash
$ vpype random --count 100 --area 10cm 10cm rotate 45 write --page-format a4 --center output.svg
```

This is how the output would look like in InkScape:

<img src="https://i.imgur.com/d9fSrRh.png" alt="100 random lines in a 10x10cm box rotated by 45 degrees" width=300>

As _vpype_ focuses only on vector graphics used as input for plotters, its data model is very simple and only includes
paths, at the exclusion of formatting (line color, width, etc.), filled shapes, bitmaps, etc. This is the core of what
makes _vpype_ both simple and powerful at what it does.  
    
This project is at the stage of the functional proof-of-concept and is being actively developed based on interest and 
feedback. It is written in Python and relies on [Click](https://palletsprojects.com/p/click/),
[Shapely](https://shapely.readthedocs.io),
[svgwrite](https://svgwrite.readthedocs.io),
[svgpathtools](https://github.com/mathandy/svgpathtools),
[matplotlib](https://matplotlib.org),
[NumPy](https://numpy.org),
[hatched](https://github.com/abey79/hatched)
and many others projects.


## Getting Started

### Installation

Install _vpype_ with the following steps, preferably in a dedicated virtual environment (see [Development
 environment](#development-environment) for an alternative install procedure if you intend to develop):

```bash
$ pip install git+https://github.com/abey79/vpype.git#egg=vpype
```

### Running examples

A few examples are available in the `examples` sub-directory, in the form of bash scripts. The script used to create
the top banner is included:

```bash
$ cd examples
$ ./alien.sh
```


### Documentation

The CLI user interface documentation is available through the `--help` option. Use `vpype --help` to see a list of
all available commands:

```text
$ vpype --help
Usage: vpype [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

Options:
  -v, --verbose
  --help         Show this message and exit.

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

  Scale the geometries.

  The origin used is the bounding box center, unless the `--centroid` or
  `--origin` options are used.

  By default, the arguments are used as relative factors (e.g. `scale 2 2`
  make the geometries twice as big in both dimensions). With `--to`, the
  arguments are interpreted as the final size. In this case, arguments
  understand the supported units (e.g. `scale --to 10cm 10cm`).

Options:
  --to                    Arguments are interpreted as absolute size instead
                          of (relative) factors.
  -p, --keep-proportions  [--to only] Maintain the geometries proportions.
  -d, --centroid          Use the centroid as origin.
  -o, --origin FLOAT...   Use a specific origin.
  --help                  Show this message and exit.
```


### Generators, filters and sinks

It is useful to consider that, at first sight, commands can be classified in three broad categories based on what they
do:

- _Generators_ create new geometries (e.g. read from a SVG, generate random lines, etc.).
- _Filters_ alter the existing geometries (e.g. translate, rotate, etc.).
- _Sinks_ use the existing geometries for display or export without modifying them.
 
Generators are typically at the beginning of the pipelines while the sinks are most commonly found at the end. This
classification is not strict though, nor it is important internally. A command could both modify existing geometries and
add new ones, and sinks don't actual "eat" geometries as the definition implies. Geometries are instead passed on, which
enables multiple sinks to be chained (e.g. first display the result, then save it to SVG).

Here is a non-exhaustive list of important commands:

- `read`: import geometries from a SVG file
- `line`, `circle`: create the corresponding primitives 
- `script`: execute a Python script to generate geometries (see [External scripts](#external-scripts))
- `hatched`: generate hatching patterns based on an image (see the [hatched project](https://github.com/abey79/hatched))
- `translate`, `rotate`, `scale`, `skew`: basic transformation commands which do exactly what you think they do
- `crop`: crop the geometries, removing everything outside of a rectangular area
- `frame`: add a simple frame around the geometries
- `show`: display the geometries in a `matplotlib` window
- `write`: save the geometries as a SVG file


### Data model and units

Being designed for plotter data, all _vpype_ understands is lines. Specifically, straight lines. This makes _vpype_ a
very poor general purpose vector graphics tool, but hopefully a decent one when dealing with graphics files sent to
plotters. When loading geometries from existing SVG file (using the `read` command), curved paths such as Bezier
curves or ellipses are converted into multiple, typically small segments. The quantization interval is 1mm by default,
but can be changed with the `--quantization` option of the `read` command.

Internally, _vpype_ use the CSS pixel as unit, which is defined as 1/96th of an inch, which happens to be the default
unit used by the SVG format. Most commands understand other standard units thought, including `in`, `cm`, `mm`, `pt` and
`pc`. These two commands thus generate the same output (100 random lines in a 1x1in square in the middle of an A4 page):

```bash
$ vpype random --count 100 --area 96 96 write --page-format a4 --center output.svg
$ vpype random --count 100 --area 1in 1in write --page-format a4 --center output.svg
```


### External scripts

The `script` command is a very useful generator that relies on an external Python script to produce geometries. Its
use is demonstrated by the `alien.sh` and `alien2.sh` examples. A path to a Python file must be passed as argument.
The file must implement a `generate()` function which returns a Shapely `MultiLineString` object. This is very easy
and explained in the [Shapely documentation](https://shapely.readthedocs.io/en/latest/manual.html#collections-of-lines).


### Blocks

Blocks refer to a portion of the pipeline marked by the `begin` and `end` special commands.
The command immediately following `begin` is called the _block processor_ and defines how many times this portion of
the pipeline will be used. For example, the `grid` block processor repeatedly execute the block and arranges the
resulting geometries on a regular NxM grid. This is how the top banner has been generated:

```bash
vpype begin \
  grid --offset 1.5cm 1.5cm 13 20 \
  script alien_letter.py \
  scale --to 0.8cm 0.8cm \
end \
write --page-format a3 --center alien.svg
```

The pipelines above mainly consist of a block with the `grid` block processor. It is repeated on the 13 by 20 grid, with
a spacing of 1.5cm in both direction. On each of these location, the script `alien_letter.py` is executed to generate
some geometries, which are then scaled to a 0.8x0.8cm size. After the block, we `write` the result to a SVG.

Notice how, with added newlines and proper indenting, the sequence of commands emerges as a kind of mini-language. You
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


## Contributing

### Development environment

The first step is to download the code:

```bash
$ git clone https://github.com/abey79/vpype.git
```

Then, create a virtual environment, update pip and install development dependencies:

```bash
$ cd vpype
$ python3 -m venv venv
$ souce venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
```

Finally, install your copy of _vpype_ as editable package:

```
$ pip install -e .
```

The `vpype` executable will then be available in the terminal and be based on the actual source. If you are using an
IDE, point its run/debug configuration to `venv/bin/bin/vpype`. 


### Running the tests

You can run tests with the following command:

```bash
$ pytest
```


### Making a contribution

This project is at an early stage and welcomes all types of contributions, such as proposal for:

- new options to current commands,
- CLI UX improvements,
- new commands and/or features, including their CLI UX,
- etc.
  
You may open [Issues](https://github.com/abey79/vpype/issues) to discuss any of this. Feel free to also open [Pull
requests](https://github.com/abey79/vpype/pulls) to contribute actual code. Note that this project uses
[`black`](https://github.com/psf/black) for code formatting so we don't have to discuss about it.


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
