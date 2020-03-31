# Understanding vpype

## Generators, filters and sinks

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
- `line`, `rect`, `circle`: create the corresponding primitives 
- `script`: execute a Python script to generate geometries (see [External scripts](#external-scripts))
- `translate`, `rotate`, `scale`, `skew`: basic transformation commands which do exactly what you think they do
- `crop`: crop the geometries, removing everything outside of a rectangular area
- `linemerge`: merge lines whose endings overlap or are very close
- `linesort`: sort lines to minimize the total distance between the end of a path to the start of the next one
- `multipass`: prepare twp-pass (or more) files for when a single stroke isn't sufficient for a good render 
- `frame`: add a simple frame around the geometries
- `show`: display the geometries in a `matplotlib` window
- `write`: save the geometries as a SVG file


## Data model and units

TODO: expend on linearisation

Being designed for plotter data, all _vpype_ understands is lines. Specifically, straight lines. This makes _vpype_ a
very poor general purpose vector graphics tool, but hopefully a good one when dealing with graphics files sent to
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


## Lengths and units

TODO: move content from previous section here


## Layers

_vpype_ supports multiple layers and can produce multi-layer SVGs, which can be useful for polychromic drawings.
Most commands have a `-l, --layer` option which affects how layers are created and/or modified.
Layers are always referred to by a non-zero, positive integer (which ties nicely with how official
[AxiDraw](https://axidraw.com) tools deal with layers).

Generators such as `read`, `line`, `script`, etc. create new geometries. The `--layer` option controls which layer receives
these new geometries. By default, the last target layer is used:
```
$ vpype line --layer 3 0 0 1cm 1cm circle 0.5cm 0.5cm 0.5cm show
``` 
Here both the line and the circle will be in layer 3. If no generator specifies a target layer, then layer 1 is assumed
by default.

Filters such as `translate`, `rotate`, `crop`, `linemerge`,  etc. modify existing geometries. The `--layer` option
controls if one, several or all layers will be affected:
```
$ vpype [...] rotate --layer 1 [...]
$ vpype [...] rotate --layer 1,2,4 [...]
$ vpype [...] rotate --layer all [...]
```
All these commands do exactly what you think they should do. If the `--layer` option is omitted, then `all` is assumed.
Note that if you provide a list of layers, they must be comma separated and without any whitespace, as the list must be
a single CLI argument.

Finally, some commands do not have a `--layer` option, but understand them. For example, `show` will display each layer
in a different color by default. Last but not least, `write` will generate multi-layer SVGs which will work 
out-of-the-box with InkScape.


## External scripts

The `script` command is a very useful generator that relies on an external Python script to produce geometries. Its
use is demonstrated by the `alien.sh` and `alien2.sh` examples. A path to a Python file must be passed as argument.
The file must implement a `generate()` function which returns a Shapely `MultiLineString` object. This is very easy
and explained in the [Shapely documentation](https://shapely.readthedocs.io/en/latest/manual.html#collections-of-lines).


## Blocks

Blocks refer to a portion of the pipeline marked by the `begin` and `end` special commands.
The command immediately following `begin` is called the _block processor_ and defines how many times this portion of
the pipeline will be used. For example, the `grid` block layer_processor repeatedly execute the block and arranges the
resulting geometries on a regular NxM grid. This is how the top banner has been generated:

```bash
vpype begin \
  grid --offset 1.5cm 1.5cm 13 20 \
  script alien_letter.py \
  scale --to 0.8cm 0.8cm \
end \
write --page-format a3 --center alien.svg
```

The pipelines above mainly consist of a block with the `grid` block layer_processor. It is repeated on the 13 by 20 grid, with
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


## Command file

When pipelines become complex, the number of command-line arguments can become too large to be convenient. To address
this, `vpype` support the inclusion of command files in the pipeline. A command file is a text file whose content is
interpreted as if it was command-line arguments.

The previous example can be converted to a command file with the following content:
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

The command file can then be loaded as argument using the `-I` or `--include` option:

```bash
$ vpype -I command_file.vpy
``` 

Newlines and indentation are ignored and useful only for readability. Everything right of a `#` character is considered
a comment and thus ignored. Command files can be mixed with regular arguments too:

```text
$ vpype -I generate_lines.vpy write -p a4 -c output.svg
```

Finally, command files can also include other command files:

```text
# Example command file
begin
  grid --offset 1cm 1cm 2 2
  -I sub_command.vpy
end
show
```


## Plug-ins

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



