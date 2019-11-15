# TODO

## Known limitations

- lack of tests
- lack of error checking in many places (e.g. script!)

## MUST BEFORE PUBLISH

- add support for float hatching pitch to hatched, and test


## Misc

- plugin interface
- python API to apply a pipeline on a MLS object and get the resulting MLS
- support for file-based CLI argument (-> mini-language)
- add progress bar
- move to PyGEOS


## Generator

- primitives: segment, square, circle, polygon
- 3D with _lines_
- _neonlines_


## Filters

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
