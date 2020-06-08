# TODO

## Misc

- command files: cwd is bugged for `read`, fix with new `pushcwd`, `popcwd` commands
- `read`: do not load "invisible" geometry
- python API to apply a pipeline on a VectorData object and get the resulting VectorData
- scribble plots: cut svg in block, shuffle block, so that plot is salvaged if pen dies at 80%

## Generator

- primitives: polygon
- 3D with _lines_

## Filters

- geometry: mask with rectangle, circle, etc.
- mask with image file + threshold (eg https://www.reddit.com/r/PlotterArt/comments/d01ro6/the_abandoned/)

## Output

- output: add `-f svg|png|...` with auto-discovery
- png
- AxiDraw api (axi?)
- Send to Saxis?
- Gcode for custom plotter?


## Block processors

- business card: arrange geometries in business card sized slots and add cut marks
