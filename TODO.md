# TODO

## Misc

- command files: cwd is bugged for `read`, fix with new `pushcwd`, `popcwd` commands
- `read`: do not load "invisible" geometry
- `show`: unit option 
- move all commands in a "command" sub-package
- plugin interface with [click-plugins](https://github.com/click-contrib/click-plugins)
- python API to apply a pipeline on a MLS object and get the resulting MLS
- move to PyGEOS?
- scribble plots: cut svg in block, shuffle block, so that plot is salvaged if pen dies at 80%


## Generator

- primitives: polygon
- 3D with _lines_
- _neonlines_ (plug-in)


## Filters

- duplicate line and reverse (https://twitter.com/EMSL/status/1196679152180416512?s=20)
- geometry: mask with rectangle, circle, etc.
- mask with image file + threshold (eg https://www.reddit.com/r/PlotterArt/comments/d01ro6/the_abandoned/)
- linemerge (axi?)


## Output

- output: add `-f svg|png|...` with auto-discovery
- png
- AxiDraw api (axi?)
- Send to Saxis?
- Gcode for custom plotter?


## Block processors

- business card: arrange geometries in business card sized slots and add cut marks
