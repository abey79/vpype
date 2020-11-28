<img src="https://i.imgur.com/LM2Qrc0.png" alt="banner" width=1200>


# _vpype_

[![PyPI](https://img.shields.io/pypi/v/vpype?label=PyPI&logo=pypi)](https://pypi.org/project/vpype/)
![python](https://img.shields.io/github/languages/top/abey79/vpype)
[![license](https://img.shields.io/github/license/abey79/vpype)](https://vpype.readthedocs.io/en/latest/license.html)
![Test](https://img.shields.io/github/workflow/status/abey79/vpype/Lint%20and%20Tests?label=Tests&logo=github)
[![Sonarcloud Status](https://sonarcloud.io/api/project_badges/measure?project=abey79_vpype&metric=alert_status)](https://sonarcloud.io/dashboard?id=abey79_vpype)
[![Documentation Status](https://img.shields.io/readthedocs/vpype?label=Read%20the%20Docs&logo=read-the-docs)](https://vpype.readthedocs.io/en/latest/?badge=latest)


TODO: TOC here!!!!


## What _vpype_ is?

_vpype_ is the Swiss-Army-knife command-line tool for processing or producing plotter-ready vector graphics.
Its typical uses includes:
 - laying out existing vector files with precise control on position, scale and page format;
 - optimizing existing SVG files for faster and cleaner plots;
 - creating HPGL output for vintage plotter;
 - creating generative artwork through built-in commands or plug-in extensions;
 - create, modify and process multi-layer vector files for multi-colour plots;
 - and much more...
 
_vpype_ is highly extensible through [plug-ins](https://vpype.readthedocs.io/en/latest/api/vpype.html#module-vpype) that
can greatly extend its capabilities. For example, plug-ins already exists for plotting
[pixel art](https://github.com/abey79/vpype-pixelart), [half-toning with hatches](https://github.com/abey79/hatched),
[plotting text](https://github.com/abey79/vpype-text) with Hershey fonts,
applying [hidden line removal](https://github.com/LoicGoulefert/occult), and much more.  

_vpype_ is also a [well documented](https://vpype.readthedocs.io/en/latest/api/vpype.html#module-vpype) Python library
useful to create generative art and tools for plotters. For example, the plotter generative art environment
[vsketch](https://github.com/abey79/vsketch) is built upon _vpype_.

Check the [documentation](https://vpype.readthedocs.io/en/latest/) for a more thorough introduction to _vpype_.

## How does it work?

_vpype_ works by building so-called _pipelines_ of _commands_, where each command's output is fed to the next command's
input.
Some commands load geometries into the pipeline (e.g.
the `read` command which loads geometries from a SVG file). Other commands modify these geometries, e.g. by cropping
them (`crop`) or reordering them to minimize pen-up travels (`linesort`). Finally, some other commands just read the
geometries in the pipeline for display purposes (`show`) or output to file (`write`).

Pipeline are defined using the _vpype_'s CLI (command-line interface) in a terminal by typing `vpype` followed by the
list of commands, each with their optional parameters and their arguments:

![command line](docs/images/command_line.png)

This pipeline uses five commands (in bold). `read` loads geometries from a SVG file, `linemerge` merges paths whose
extremities are close to each other (within the provided tolerance), `linesort` reorder paths such as to minimise the
pen-up travel, `crop`, well, crops, and `write` export the resulting geometries to a SVG file.

Some commands have arguments, which are always required (in italic). For example, a file path must be provided to the
`read` command and dimensions must be provided to the `crop` commands. Commands may also have options which are, well,
optional. In this example, `--page-size a4` means that the `write` command will generate a A4-sized SVG (otherwise it
would have the same size as `in.svg`). Likewise, because `--center` is used, the `write` command will center geometries
on the page before saving the SVG (otherwise the geometries would have been left at their original location on page).


## Examples

Load an SVG file, scale it to a specific size, and export it centered on an A4-sized, ready-to-plot SVG file:
```bash
vpype read input.svg scaleto 10cm 10cm write --page-size a4 --center output.svg
```

Optimize paths to reduce plotting time (merge connected lines and sort them to minimize pen-up distance):
```bash
vpype read input.svg linemerge --tolerance 0.1mm linesort write output.svg
```

Visualize the path structure of large SVG files, showing whether lines are properly joined or not thanks to a colorful
display:
```bash
vpype read input.svg show --colorful
```

Load several SVG files and save them as a single, multi-layer SVG file (e.g. for multicolored drawings):
```bash
vpype read -l 1 input1.svg read -l 2 input2.svg write output.svg
```

Create arbitrarily-sized, grid-like designs like this page's top banner:
```bash
vpype begin grid -o 1cm 1cm 10 13 script alien_letter.py scaleto 0.5cm 0.5cm end show
```

Export to HPGL for vintage plotters:
```bash
vpype read input.svg write --device hp7475a --page-size a4 --landscape --center output.hpgl
```
  
## What _vpype_ isn't?

_vpype_ caters to plotter generative art and does not aim to be a general purpose (think
Illustrator/InkScape) vector graphic tools. One of the main reason for this is the fact _vpype_ converts everything 
curvy (circles, bezier curves, etc.) to lines made of small segments. _vpype_ also dismisses the stroke and fill
properties (color, line width, etc.) of the imported graphics. These design choices make possible _vpype_'s rich feature
set, but makes its use for, e.g., printed media limited. 
 
 
## Installation

In a nutshell:
```bash
pip install vpype
```

Check [the documentation](https://vpype.readthedocs.io/en/latest/install.html) for more details.

## Documentation

The _vpype_ CLI includes its own, detailed documentation:

```bash
vpype --help          # general help and command list
vpype COMMAND --help  # help for a specific command
``` 

In addition, the [online documentation](https://vpype.readthedocs.io/en/latest/) provides extensive background
information on the fundamentals behind _vpype_, a cookbook covering most common tasks, the _vpype_ API documentation,
and much more.


## Feature overview

#### General

- Easy to use **CLI** interface with integrated help (`vpype --help`and `vpype COMMAND --help`) and support for arbitrary units (e.g. `vpype read input.svg translate 3cm 2in`).
- First-class **multi-layer support** with global or per-layer processing (e.g. `vpype COMMANDNAME --layer 1,3`) and layer edition commands ([`lmove`](https://vpype.readthedocs.io/en/latest/reference.html#lmove), [`lcopy`](https://vpype.readthedocs.io/en/latest/reference.html#lcopy), [`ldelete`](https://vpype.readthedocs.io/en/latest/reference.html#ldelete)).
- Powerful **display** command with adjustable units, optional per-line coloring, optional pen-up trajectories display and per-layer visibility control ([`show`](https://vpype.readthedocs.io/en/latest/reference.html#show)).
- Geometry **statistics** extraction ([`stat`](https://vpype.readthedocs.io/en/latest/reference.html#stat)).
- Support for  **command history** recording (`vpype -H [...]`)
- Support for **RNG seed** configuration for generative plug-ins (`vpype -s 37 [...]`).


#### Input/Output

- Single- and multi-layer **SVG input** with adjustable precision, parallel processing for large SVGs, and supports percent or missing width/height ([`read`](https://vpype.readthedocs.io/en/latest/reference.html#read)).
- Support for **SVG output** with fine layout control (page size and orientation, centering), layer support with custom layer names, optional display of pen-up trajectories, various option for coloring ([`write`](https://vpype.readthedocs.io/en/latest/reference.html#write)).
- Support for **HPGL output** config-based generation of HPGL code with fine layout control (page size and orientation, centering).


#### Layout and transforms

- Powerful **transform** commands for scaling, translating, skewing and rotating geometries ([`scale`](https://vpype.readthedocs.io/en/latest/reference.html#scale), [`translate`](https://vpype.readthedocs.io/en/latest/reference.html#translate), [`skew`](https://vpype.readthedocs.io/en/latest/reference.html#skew), [`rotate`](https://vpype.readthedocs.io/en/latest/reference.html#rotate)).
- Support for **scaling** and **cropping** to arbitrary dimensions ([`scaleto`](https://vpype.readthedocs.io/en/latest/reference.html#scaleto), [`crop`](https://vpype.readthedocs.io/en/latest/reference.html#crop)).
- Support for **trimming** geometries by an arbitrary amount ([`trim`](https://vpype.readthedocs.io/en/latest/reference.html#trim)).
- Arbitrary **page size** definition ([`pagesize`](https://vpype.readthedocs.io/en/latest/reference.html#pagesize)). 


#### Plotting optimization

- **Line merging** with optional path reversal and configurable merging threshold ([`linemerge`](https://vpype.readthedocs.io/en/latest/reference.html#linemerge)).
- **Line sorting** with optional path reversal ([`linesort`](https://vpype.readthedocs.io/en/latest/reference.html#linesort)).
- **Line simplification** with adjustable accuracy ([`linesimplify`](https://vpype.readthedocs.io/en/latest/reference.html#linesimplify)).
- Support for **splitting** all lines to their constituent segments ([`splitall`](https://vpype.readthedocs.io/en/latest/reference.html#splitall)).
- Closed paths' **seam location randomization**, to reduce the visibility of pen-up/pen-down artifacts ([`reloop`](https://vpype.readthedocs.io/en/latest/reference.html#reloop)).
- Support for generating **multiple passes** on each line ([`multipass`](https://vpype.readthedocs.io/en/latest/reference.html#multipass)).
- Support for **filtering** by line lengths or closed-ness ([`filter`](https://vpype.readthedocs.io/en/latest/reference.html#filter)).
 
 #### Generation
 
 - Generation of arbitrary **primitives** including lines, rectangles, circles, ellipses and arcs ([`line`](https://vpype.readthedocs.io/en/latest/reference.html#line), [`rect`](https://vpype.readthedocs.io/en/latest/reference.html#rect), [`circle`](https://vpype.readthedocs.io/en/latest/reference.html#circle), [`ellipse`](https://vpype.readthedocs.io/en/latest/reference.html#ellipse), [`arc`](https://vpype.readthedocs.io/en/latest/reference.html#arc)).
 - Generation of grid-like layouts ([`grid`](https://vpype.readthedocs.io/en/latest/reference.html#grid)).
 - Generation of a **frame** around the geometries ([`frame`](https://vpype.readthedocs.io/en/latest/reference.html#frame)).
 - Generation of random lines for debug/learning purposes ([`random`](https://vpype.readthedocs.io/en/latest/reference.html#random))

#### Extensibility and API

 - First-class support for **plug-in** extensions (e.g [vpype-text](https://github.com/abey79/vpype-text), [hatched](https://github.com/abey79/hatched), [occult](https://github.com/LoicGoulefert/occult)).
 - Support for **script-based** generation ([`script`](https://vpype.readthedocs.io/en/latest/reference.html#script)).
 - Powerful and [well-documented](https://vpype.readthedocs.io/en/latest/api/vpype.html#module-vpype) **API** for plug-ins and other plotter generative art projects.
 
 
 ## Contributing

Contributions to this project are welcome and do not necessarily require software development skills! Check the
[Contributing section](https://vpype.readthedocs.io/en/latest/contributing.html) of the documentation for more
information.  


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.



# TO MERGE TO THE DOC


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
