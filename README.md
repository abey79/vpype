![banner](https://github.com/abey79/vpype/raw/master/docs/images/banner_ua.png)


# _vpype_

[![PyPI](https://img.shields.io/pypi/v/vpype?label=PyPI&logo=pypi)](https://pypi.org/project/vpype/)
[![python](https://img.shields.io/github/languages/top/abey79/vpype)](https://www.python.org)
[![Downloads](https://pepy.tech/badge/vpype)](https://pepy.tech/project/vpype)
[![license](https://img.shields.io/pypi/l/vpype)](https://vpype.readthedocs.io/en/latest/license.html)
![Test](https://img.shields.io/github/actions/workflow/status/abey79/vpype/python-lint-tests.yml?branch=master)
[![codecov](https://codecov.io/gh/abey79/vpype/branch/master/graph/badge.svg?token=CE7FD9D6XO)](https://codecov.io/gh/abey79/vpype)
[![Sonarcloud Status](https://sonarcloud.io/api/project_badges/measure?project=abey79_vpype&metric=alert_status)](https://sonarcloud.io/dashboard?id=abey79_vpype)
[![Documentation Status](https://img.shields.io/readthedocs/vpype?label=Read%20the%20Docs&logo=read-the-docs)](https://vpype.readthedocs.io/en/latest/?badge=latest)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

_vpype_ is the Swiss-Army-knife command-line tool for plotter vector graphics.

#### Contents

* [What _vpype_ is?](#what-vpype-is)
* [How does it work?](#how-does-it-work)
* [Examples](#examples)
* [What _vpype_ isn't?](#what-vpype-isnt)
* [Installation](#installation)
* [Documentation](#documentation)
* [Feature overview](#feature-overview)
    * [General](#general)
    * [Input/Output](#inputoutput)
    * [Layout and transforms](#layout-and-transforms)
    * [Plotting optimization](#plotting-optimization)
    * [Generation](#generation)
    * [Extensibility and API](#extensibility-and-api)
* [Plug-ins](#plug-ins)
* [Contributing](#contributing)
* [License](#license)


## What _vpype_ is?

_vpype_ is the Swiss-Army-knife command-line tool for plotter vector graphics. Here is what it can do:
 - **layout** existing vector files with precise control on position, scale and page format;
 - **optimize** existing SVG files for faster and cleaner plots;
 - create **HPGL output** for vintage plotters;
 - create **generative artwork** from scratch through built-in commands or [plug-ins](#plug-ins);
 - create, modify and process **multi-layer vector files** for multi-colour plots;
 - and much more...
 
_vpype_ is highly **extensible** through plug-ins that can greatly extend its capabilities. For example, plug-ins
already exists for plotting [pixel art](https://github.com/abey79/vpype-pixelart),
[half-toning with hatches](https://github.com/abey79/hatched), and much more. See below for a
[list of existing plug-ins](#plug-ins).

_vpype_ is also a [well documented](https://vpype.readthedocs.io/en/latest/api.html) **Python library**
useful to create generative art and tools for plotters. It includes data structures, utility and I/O functions, as well as
a hardware-accelerated flexible viewer for vector graphics. For example, the plotter generative art environment
[vsketch](https://github.com/abey79/vsketch) is built upon _vpype_.

Check the [documentation](https://vpype.readthedocs.io/en/latest/) for a more thorough introduction to _vpype_.

## How does it work?

_vpype_ works by building so-called _pipelines_ of _commands_, where each command's output is fed to the next command's input.
Some commands load geometries into the pipeline (e.g. the [`read`](https://vpype.readthedocs.io/en/latest/reference.html#read)
command which loads geometries from a SVG file). Other commands modify these geometries, e.g. by cropping
them ([`crop`](https://vpype.readthedocs.io/en/latest/reference.html#crop)) or reordering them to minimize pen-up
travels ([`linesort`](https://vpype.readthedocs.io/en/latest/reference.html#linesort)). Finally, some other commands
just read the geometries in the pipeline for display purposes ([`show`](https://vpype.readthedocs.io/en/latest/reference.html#show))
or output to file ([`write`](https://vpype.readthedocs.io/en/latest/reference.html#write)).

Pipeline are defined using the _vpype_'s CLI (command-line interface) in a terminal by typing `vpype` followed by the
list of commands, each with their optional parameters and their arguments:

![command line](https://github.com/abey79/vpype/raw/master/docs/images/command_line.svg)

This pipeline uses five commands (in bold):
- [`read`](https://vpype.readthedocs.io/en/latest/reference.html#read) loads geometries from a SVG file.
- [`linemerge`](https://vpype.readthedocs.io/en/latest/reference.html#linemerge) merges paths whose extremities are close to each other (within the provided tolerance).
- [`linesort`](https://vpype.readthedocs.io/en/latest/reference.html#linesort) reorder paths such as to minimise the pen-up travel.
- [`crop`](https://vpype.readthedocs.io/en/latest/reference.html#crop), well, crops.
- [`write`](https://vpype.readthedocs.io/en/latest/reference.html#write) export the resulting geometries to a SVG file.

There are many more commands available in *vpype*, see the [overview](#feature-overview) below.

Some commands have arguments, which are always required (in italic). For example, a file path must be provided to the
[`read`](https://vpype.readthedocs.io/en/latest/reference.html#read) command and dimensions must be provided to the [`crop`](https://vpype.readthedocs.io/en/latest/reference.html#crop) commands. A command may also have options which are, well,
optional. In this example, `--page-size a4` means that the [`write`](https://vpype.readthedocs.io/en/latest/reference.html#write) command will generate a A4-sized SVG (otherwise it
would have the same size as _in.svg_). Likewise, because `--center` is used, the [`write`](https://vpype.readthedocs.io/en/latest/reference.html#write) command will center geometries
on the page before saving the SVG (otherwise the geometries would have been left at their original location).


## Examples

**Note**: The following examples are laid out over multiple lines using end-of-line escaping (`\`). This is done to highlight the various commands of which the pipeline is made and would typically not be done in real-world use. 

Load an SVG file, scale it to a specific size, and export it centered on an A4-sized, ready-to-plot SVG file:
```bash
$ vpype \
  read input.svg \
  layout --fit-to-margins 2cm a4 \
  write output.svg
```

Optimize paths to reduce plotting time (merge connected lines, sort them to minimize pen-up distance, randomize closed paths' seam, and reduce the number of nodes):
```bash
$ vpype \
  read input.svg \
  linemerge --tolerance 0.1mm \
  linesort \
  reloop \
  linesimplify \
  write output.svg
```

Load a SVG and display it in *vpype*'s viewer, which enable close inspection of the layer and path structure):
```bash
$ vpype \
  read input.svg \
  show
```

Load several SVG files and save them as a single, multi-layer SVG file (e.g. for multicolored drawings):
```bash
$ vpype \
  forfile "*.svg" \
    read --layer %_i% %_path% \
  end \
  write output.svg
```

Export a SVG to HPGL for vintage plotters:
```bash
$ vpype \
  read input.svg \
  layout --fit-to-margins 2cm --landscape a4 \
  write --device hp7475a output.hpgl
```

Draw the layer name on a SVG (this example uses [property substitution](https://vpype.readthedocs.io/en/latest/fundamentals.html#property-substitution)):
```bash
$ vpype \
    read input.svg \
    text --layer 1 "{vp_name}" \
    write output.svg
```

Merge multiple SVG files in a grid layout (this example uses [expression substitution](https://vpype.readthedocs.io/en/latest/fundamentals.html#expression-substitution)):
```bash
$ vpype \
    eval "files=glob('*.svg')" \
    eval "cols=3; rows=ceil(len(files)/cols)" \
    grid -o 10cm 10cm "%cols%" "%rows%" \
        read --no-fail "%files[_i] if _i < len(files) else ''%" \
        layout -m 0.5cm 10x10cm \
    end \
    write combined_on_a_grid.svg
```

An interactive version of the previous example is available in `examples/grid.vpy`. It makes use of `input()` expressions to ask parameters from the user:
```bash
$ vpype -I examples/grid.vpy
Files [*.svg]?
Number of columns [3]? 4
Column width [10cm]?
Row height [10cm]? 15cm
Margin [0.5cm]?
Output path [output.svg]?
```

Split a SVG into one file per layer:
```bash
$ vpype \
    read input.svg \
    forlayer \
      write "output_%_name or _lid%.svg" \
    end
```

More examples and recipes are available in the [cookbook](https://vpype.readthedocs.io/en/latest/cookbook.html). 
  
## What _vpype_ isn't?

_vpype_ caters to plotter generative art and does not aim to be a general purpose (think
Illustrator/InkScape) vector graphic tools. One of the main reason for this is the fact _vpype_ converts everything 
curvy (circles, bezier curves, etc.) to lines made of small segments. _vpype_ does import metadata such stroke and fill color, stroke width, etc., it only makes partial use of them and does not aim to maintain a full consistency with the SVG specification. These design choices make _vpype_'s rich feature set possible, but limits its use for, e.g., printed media. 
 
 
## Installation

Detailed installation instructions are available in the [latest documentation](https://vpype.readthedocs.io/en/latest/install.html).

TL;DR:
- Python 3.13 is recommended, but *vpype* is also compatible with Python 3.11 and 3.12. 
- *vpype* is published on the [Python Package Index](https://pypi.org) and can be installed using [pipx](https://pypa.github.io/pipx/):
  ```bash
  pipx install "vpype[all]"
  ```
- A Windows installer is available [here](https://github.com/abey79/vpype/releases), but plug-ins cannot be installed
when using this method).
- A CLI-only version of *vpype* can be installed using the following command:
  ```bash
  pipx install vpype
  ```
  This version does not include the [`show`](https://vpype.readthedocs.io/en/latest/reference.html#show) command but does not require some of the dependencies which are more difficult or impossible to install on some platforms (such as matplotlib, PySide6, and ModernGL).


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
- First-class **multi-layer support** with global or per-layer processing (e.g. `vpype COMMANDNAME --layer 1,3`) and optionally-probabilistic layer edition commands ([`lmove`](https://vpype.readthedocs.io/en/latest/reference.html#lmove), [`lcopy`](https://vpype.readthedocs.io/en/latest/reference.html#lcopy), [`ldelete`](https://vpype.readthedocs.io/en/latest/reference.html#ldelete), [`lswap`](https://vpype.readthedocs.io/en/latest/reference.html#lswap), [`lreverse`](https://vpype.readthedocs.io/en/latest/reference.html#lreverse)).
- Support for **per-layer and global properties**, which acts as metadata and is used by multiple commands and plug-ins.
- Support for [**property**](https://vpype.readthedocs.io/en/latest/fundamentals.html#property-substitution) and [**expression substitution**](https://vpype.readthedocs.io/en/latest/fundamentals.html#expression-substitution) in CLI user input.
- Support for complex, **per-layer** processing ([`perlayer`](https://vpype.readthedocs.io/en/latest/reference.html#perlayer)).
- Powerful hardware-accelerated **display** command with adjustable units, optional per-line coloring, optional pen-up trajectories display and per-layer visibility control ([`show`](https://vpype.readthedocs.io/en/latest/reference.html#show)).
- Geometry **statistics** extraction ([`stat`](https://vpype.readthedocs.io/en/latest/reference.html#stat)).
- Support for  **command history** recording (`vpype -H [...]`)
- Support for **RNG seed** configuration for generative plug-ins (`vpype -s 37 [...]`).


#### Input/Output

- Single- and multi-layer **SVG input** with adjustable precision, parallel processing for large SVGs, and supports percent or missing width/height ([`read`](https://vpype.readthedocs.io/en/latest/reference.html#read)).
- Support for **SVG output** with fine layout control (page size and orientation, centering), layer support with custom layer names, optional display of pen-up trajectories, various option for coloring ([`write`](https://vpype.readthedocs.io/en/latest/reference.html#write)).
- Support for **HPGL output** config-based generation of HPGL code with fine layout control (page size and orientation, centering).
- Support for pattern-based **file collection** processing ([`forfile`](https://vpype.readthedocs.io/en/latest/reference.html#forfile)). 


#### Layout and transforms

- Easy and flexible **layout** command for centring and fitting to margin with selectable le horizontal and vertical alignment
  ([`layout`](https://vpype.readthedocs.io/en/latest/reference.html#layout)).
- **Page rotation** command ([`pagerotate`](https://vpype.readthedocs.io/en/latest/reference.html#pagerotate)).
- Powerful **transform** commands for scaling, translating, skewing and rotating geometries ([`scale`](https://vpype.readthedocs.io/en/latest/reference.html#scale), [`translate`](https://vpype.readthedocs.io/en/latest/reference.html#translate), [`skew`](https://vpype.readthedocs.io/en/latest/reference.html#skew), [`rotate`](https://vpype.readthedocs.io/en/latest/reference.html#rotate)).
- Support for **scaling** and **cropping** to arbitrary dimensions ([`scaleto`](https://vpype.readthedocs.io/en/latest/reference.html#scaleto), [`crop`](https://vpype.readthedocs.io/en/latest/reference.html#crop)).
- Support for **trimming** geometries by an arbitrary amount ([`trim`](https://vpype.readthedocs.io/en/latest/reference.html#trim)).
- Arbitrary **page size** definition ([`pagesize`](https://vpype.readthedocs.io/en/latest/reference.html#pagesize)). 


#### Metadata

- Adjust layer **color**, **alpha**, **pen width** and **name** ([`color`](https://vpype.readthedocs.io/en/latest/reference.html#color), [`alpha`](https://vpype.readthedocs.io/en/latest/reference.html#alpha), [`penwidth`](https://vpype.readthedocs.io/en/latest/reference.html#penwidth), [`name`](https://vpype.readthedocs.io/en/latest/reference.html#name)).
- Apply provided or fully customisable **pen configurations** ([`pens`](https://vpype.readthedocs.io/en/latest/reference.html#pens)).
- Manipulate global and per-layer **properties** ([`propset`](https://vpype.readthedocs.io/en/latest/reference.html#propset), [`propget`](https://vpype.readthedocs.io/en/latest/reference.html#propget), [`proplist`](https://vpype.readthedocs.io/en/latest/reference.html#proplist), [`propdel`](https://vpype.readthedocs.io/en/latest/reference.html#propdel), [`propclear`](https://vpype.readthedocs.io/en/latest/reference.html#propclear)).


#### Plotting optimization

- **Line merging** with optional path reversal and configurable merging threshold ([`linemerge`](https://vpype.readthedocs.io/en/latest/reference.html#linemerge)).
- **Line sorting** with optional path reversal ([`linesort`](https://vpype.readthedocs.io/en/latest/reference.html#linesort)).
- **Line simplification** with adjustable accuracy ([`linesimplify`](https://vpype.readthedocs.io/en/latest/reference.html#linesimplify)).
- Closed paths' **seam location randomization**, to reduce the visibility of pen-up/pen-down artifacts ([`reloop`](https://vpype.readthedocs.io/en/latest/reference.html#reloop)).
- Support for generating **multiple passes** on each line ([`multipass`](https://vpype.readthedocs.io/en/latest/reference.html#multipass)).

#### Filters

- Support for **filtering** by line lengths or closed-ness ([`filter`](https://vpype.readthedocs.io/en/latest/reference.html#filter)).
- **Squiggle** filter for shaky-hand or liquid-like styling ([`squiggles`](https://vpype.readthedocs.io/en/latest/reference.html#squiggles))
- Support for **splitting** all lines to their constituent segments ([`splitall`](https://vpype.readthedocs.io/en/latest/reference.html#splitall)).
- Support for **reversing** order of paths within their layers ([`reverse`](https://vpype.readthedocs.io/en/latest/reference.html#reverse)).
- Support for **splitting** layers by drawing distance ([`splitdist`](https://vpype.readthedocs.io/en/latest/reference.html#splitdist))

#### Generation
 
 - Generation of arbitrary **primitives** including lines, rectangles, circles, ellipses and arcs ([`line`](https://vpype.readthedocs.io/en/latest/reference.html#line), [`rect`](https://vpype.readthedocs.io/en/latest/reference.html#rect), [`circle`](https://vpype.readthedocs.io/en/latest/reference.html#circle), [`ellipse`](https://vpype.readthedocs.io/en/latest/reference.html#ellipse), [`arc`](https://vpype.readthedocs.io/en/latest/reference.html#arc)).
 - Generation of **text** using bundled Hershey fonts ([`text`](https://vpype.readthedocs.io/en/latest/reference.html#text))
 - Generation of grid-like layouts ([`grid`](https://vpype.readthedocs.io/en/latest/reference.html#grid)).
 - Generation of a **frame** around the geometries ([`frame`](https://vpype.readthedocs.io/en/latest/reference.html#frame)).
 - Generation of random lines for debug/learning purposes ([`random`](https://vpype.readthedocs.io/en/latest/reference.html#random))

#### Extensibility and API

 - First-class support for **plug-in** extensions (e.g [vpype-text](https://github.com/abey79/vpype-text), [hatched](https://github.com/abey79/hatched), [occult](https://github.com/LoicGoulefert/occult)).
 - Support for **script-based** generation ([`script`](https://vpype.readthedocs.io/en/latest/reference.html#script)).
 - Powerful and [well-documented](https://vpype.readthedocs.io/en/latest/api.html) **API** for plug-ins and other plotter generative art projects.
 
 
 ## Plug-ins
 
 Here is a list of known vpype plug-ins (please make a pull request if yours is missing):
 
 - [vsketch](https://github.com/abey79/vsketch): *vsketch* is complete framework for plotter generative artists implemented using *vpype*'s API
 - [vpype-perspective](https://github.com/abey79/vpype-perspective): put your art in perspective
 - [vpype-pixelart](https://github.com/abey79/vpype-pixelart): plot pixel art
 - [hatched](https://github.com/abey79/hatched): half-toning with hatches
 - [vpype-flow-imager](https://github.com/serycjon/vpype-flow-imager): convert images to flow-line-based designs
 - [occult](https://github.com/LoicGoulefert/occult): perform hidden line removal
 - [deduplicate](https://github.com/LoicGoulefert/deduplicate): remove duplicate lines
 - [vpype-explorations](https://github.com/abey79/vpype-explorations): my personal grab bag of experiments and utilities
 - [vpype-gcode](https://github.com/tatarize/vpype-gcode/): flexible export command for gcode and other text-based format
 - [vpype-dxf](https://github.com/tatarize/vpype-dxf/): read dxf files
 - [vpype-embroidery](https://github.com/EmbroidePy/vpype-embroidery): various embroidery-related utilities, including read from/write to most embroidery formats 
 - [vpype-vectrace](https://github.com/tatarize/vpype-vectrace): create outlines from images with vector tracing
 - [vpype-ttf](https://github.com/johnbentcope/vpype-ttf): create text outlines using TTF fonts
 - [vpype-gscrib](https://github.com/joansalasoler/vpype-gscrib): generate G-code for CNC machines, plotters, laser cutters, 3D printers, and more using the Gscrib library
 
 
 ## Contributing

Contributions to this project are welcome and do not necessarily require software development skills! Check the
[Contributing section](https://vpype.readthedocs.io/en/latest/contributing.html) of the documentation for more
information.  


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
