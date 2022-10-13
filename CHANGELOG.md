# Change log

## 1.12

Release date: UNRELEASED

### New features and improvements

* The `layout` command now properly handles the `tight` special case by fitting the page size around the existing geometries, accommodating for a margin if provided (#556)
* Added new units (`yd`, `mi`, and `km`) (#541)
* Added `inch` unit as a synonym to `in`, useful for expressions (in which `in` is a reserved keyword) (#541)
* Migrated to PySide6 (from PySide2), which simplifies installation on Apple silicon Macs (#552)

### Bug fixes

* Fixed a viewer issue where page width/height of 0 would lead to errors and a blank display (#555)

### API changes

* Added `vpype.format_length()` to convert pixel length into human-readable string with units (#541)

### Other changes

* Updated [svgelements](https://github.com/meerk40t/svgelements) to 1.8.4, which fixes issue with some SVG constructs used by Matplotlib exports (#549)
* [Poetry](https://python-poetry.org) 1.2 or later is not required (developer only) (#541)
* A `justfile` is now provided for most common operations (install, build the documentation, etc.) (#541)
* Migrated to [Plausible.io](https://plausible.io) (from Google Analytics) for [vpype.readthedocs.io](https://vpype.readthedocs.io) (#546)


## 1.11

Release date: 2022-07-06

[Annotated Release Notes](https://bylr.info/articles/2022/07/06/annotated-release-notes-vpype-1.11/)

### New features and improvements

* Added the `splitdist` command to split layers by drawing distance (thanks to @LoicGoulefert) (#487, #501)
* Added `--keep-page-size` option to `grid` command (#506)
* Added meters (`m`) and feet (`ft`) to the supported units (#498, #508)
* Improved the `linemerge` algorithm by making it less dependent on line order (#496)
* Added HPGL configurations for the Houston Instrument DMP-161, HP7550, Roland DXY 1xxxseries and sketchmate plotters (thanks to @jimmykl and @ithinkido) (#472, #474)
* The `forfile` command now sorts the files by their name before processing them (#506)

### Bug fixes

* Fixed an issue with blocks where certain nested commands could lead totally unexpected results (#506)
* Fixed an issue with the `lmove` command where order would not be respected in certain cases such as `lmove all 2` (the content of layer 2 was placed before that of layer 1) (#506)
* Fixed an issue with expressions where some variable names corresponding to units (e.g. `m`) could not be used (expressions may now reuse these names) (#506)

### API changes

* Removed the faulty `temp_document()` context manager from `vpype_cli.State()` (#506)
* Added equality operator to `vpype.LineCollection` and `vpype.Document` (#506)

### Other changes

* Removed dependence on `setuptools` (#454, #468)
* Pinned Shapely to 1.8.2, which is the first release in a long time to have binaries for most platforms/Python release combination (including Apple-silicon Macs and Python 3.10) (#475)
* Removed deprecated API (#507)


## 1.10

Release date: 2022-04-07

[Annotated Release Notes](https://bylr.info/articles/2022/04/07/annotated-release-notes-vpype-1.10/)

### New features and improvements

* Added the `alpha` command to set layer opacity without changing the base color (#447, #451)
* Improved support for layer pen width and opacity in the viewer (#448)

  * The "Pen Width" and "Pen Opacity" menus are now named "Default Pen Width" and "Default Pen Opacity". 
  * The layer opacity is now used for display by default. It can be overridden by the default pen opacity by checking the "Override" item from the "Default Pen Opacity" menu.
  * The layer pen width is now used for display by default as well. Likewise, it can be overridden by checking the "Override" item from the "Default Pen Width" menu.

* Added HPGL configuration for the Calcomp Artisan plotter (thanks to Andee Collard and @ithinkido) (#418)
* Added the `--dont-set-date` option to the `write` command (#442)
* The `read` command now better handles SVGs with missing `width` or `height` attributes (#446)

  When the `width` or `height` attribute is missing or expressed as percent, the `read` command now attempts to use the `viewBox` attribute to set the page size, defaulting to 1000x1000px if missing. This behavior can be overridden with the `--display-size` and the `--display-landscape` parameters. 


### Bug fixes

* Fixed an issue with `forlayer` where the `_n` variable was improperly set (#443)
* Fixed an issue with `write` where layer opacity was included in the `stroke` attribute instead of using `stroke-opacity`, which, although compliant, was not compatible with Inkscape (#429)
* Fixed an issue with `vpype --help` where commands from plug-ins would not be listed (#444)
* Fixed a minor issue where plug-ins would be reloaded each time `vpype_cli.execute()` is called (#444)
* Fixed a rendering inconsistency in the viewer where the ruler width could vary by one pixel depending on the OpenGL driver/GPU/OS combination (#448)


### API changes

* Changed the parameter name of both `vpype_viewer.Engine()` and `vpype_viewer.render_image()` from `pen_width` and `pen_opacity` to `default_pen_width` and `default_pen_opacity` (breaking change) (#448)
* Added `override_pen_width` and `override_pen_opacity` boolean parameters to both `vpype_viewer.Engine()` and `vpype_viewer.render_image()` (#448)
* Added `vpype_cli.FloatType()`, `vpype_cli.IntRangeType()`, `vpype_cli.FloatRangeType()`, and `vpype_cli.ChoiceType()` (#430, #447)
* Changed `vpype.Document.add_to_sources()` to also modify the `vp_source` property (#431)
* Added a `set_date:bool = True` argument to `vpype.write_svg()` (#442)
* Changed the default value of `default_width` and `default_height` arguments of `vpype.read_svg()` (and friends) to `None` to allow `svgelement` better handle missing `width`/`height` attributes (#446)


### Other changes

* Added support for Python 3.10 and dropped support for Python 3.7 (#417)
* Miscellaneous code cleaning and fixes (#440, 906087b)
* Updated installation instructions to use pipx (#428)
* Updated the [documentation](https://vpype.readthedocs.io/en/latest/) template (#428)
* Updated code base with modern typing syntax (using [pyupgrade](https://github.com/asottile/pyupgrade)) (#427)


## 1.9

Release date: 2022-03-03

[Annotated Release Notes](https://bylr.info/articles/2022/03/03/annotated-release-notes-vpype-1.9/)

**Note**: This is the last version of *vpype* to support Python 3.7.

### New features and improvements

* Added support for global and per-layer [properties](https://vpype.readthedocs.io/en/latest/fundamentals.html#properties) (#359)
  
  This feature introduces metadata to the pipeline in the form of properties which may either be attached to specific layers (layer property) or all of them (global property). Properties are identified by a name and may be of arbitrary type (e.g. integer, floating point, color, etc.). A number of [system properties](https://vpype.readthedocs.io/en/latest/fundamentals.html#system-properties) with a specific name (prefixed with `vp_`) and type are introduced to support some of the new features.

* Layer color, pen width, and name are now customizable (#359, #376, #389)
  * The `read` commands now sets layer color, pen width, and name based on the input SVG if possible.
  * The new `color`, `penwdith`, and `name` commands can be used to modify layer color, pen width, and name.
  * The new `pens` command can apply a predefined or custom scheme on multiple layers at once. Two common schemes are built-in: `rgb` and `cmyk`. [Custom schemes](https://vpype.readthedocs.io/en/latest/cookbook.html#creating-a-custom-pen-configuration) can be defined in the configuration file.
  * The `show` and `write` commands now take into account these layer properties.

* The `read` command now records the source SVG paths in the `vp_source` and `vp_sources` system properties (see the [documentation](https://vpype.readthedocs.io/en/latest/fundamentals.html#system-properties)) (#397, #406, #408)

* Added [property substitution](https://vpype.readthedocs.io/en/latest/fundamentals.html#property-substitution) to CLI user input (#395)

  The input provided to most commands' arguments and options may now contain substitution patterns which will be replaced by the corresponding property value. Property substitution patterns are marked with curly braces (e.g. `{property_name}`) and support the same formatting capabilities as the Python's [`format()` function](https://docs.python.org/3/library/string.html#formatstrings).

* Added [expression substitution](https://vpype.readthedocs.io/en/latest/fundamentals.html#expression-substitution) to CLI user input (#397)

  The input provided to most command's arguments and options may now contain expression patterns which are evaluated before the command is executed. Expression patterns are marked with the percent symbol `%` (e.g. `%3+4%`) and support a large subset of the Python language. [A](https://vpype.readthedocs.io/en/latest/cookbook.html#load-multiple-files-merging-their-layers-by-name) [lot](https://vpype.readthedocs.io/en/latest/cookbook.html#cropping-and-framing-geometries) [of](https://vpype.readthedocs.io/en/latest/cookbook.html#laying-out-multiple-svgs-on-a-grid) [examples](https://vpype.readthedocs.io/en/latest/cookbook.html#create-interactive-scripts-with-input) were added in the [cookbook](https://vpype.readthedocs.io/en/latest/cookbook.html).

* Added the `--attr` option to the `read` command to (optionally) sort geometries by attributes (e.g. stroke color, stroke width, etc.) instead of by SVG layer (#378, #389)

* The `read` and `write` commands now preserve a sub-set of SVG attributes (experimental) (#359, #389)
  
  The `read` command identifies SVG attributes (e.g. `stroke-dasharray`) which are common in all geometries within each layer. These attributes are saved as layer properties with their name prefixed with `svg_` (e.g. `svg_stroke-dasharray`). The `write` command can optionally restore these attributes in the output SVG using the `--restore-attribs` option.

* Introduced new commands for low-level inspection and modification of properties (#359)

  * `propget`: gets the value of a given global or layer property
  * `proplist`: lists all global and/or layer properties and their value
  * `propset`: sets the value of a given global or layer property
  * `propdel`: deletes a given global or layer property
  * `propclear`: removes all global and/or layer properties

* Updated layer operation commands to handle properties (#359)

  * When a single source layer is specified and `--prob` is not used, the `lcopy` and `lmove` commands now copy the source layer's properties to the destination layer (possibly overwriting existing properties).
  * When `--prob` is not used, the `lswap` command now swaps the layer properties as well.
  * These behaviors can be disabled with the `--no-prop` option.

* Improved block processors (#395, #397)

  * Simplified and improved the infrastructure underlying block processors for better extensibility.
  * The `begin` marker is now optional and implied whenever a block processor command is encountered. *Note*: the `end` marker must always be used to mark the end of a block.
  * Commands inside the block now have access to the current layer structure and its metadata.

* Improved the `grid` block processor (#397)
  
  * The page size is now updated according to the grid size.
  * The command now sets expression variables for use in the nested pipeline.
  * Cells are now first iterated along rows instead of columns.

* The `repeat` block processor now sets expression variables for use in the nested pipeline (#397)
* Added `forfile` block processor to iterate over a list of file (#397)
* Added `forlayer` block processor to iterate over the existing layers (#397)
* Added the `eval` command as placeholder for executing expressions (#397)
* The `read` command now will ignore a missing file if `--no-fail` parameter is used (#397)
  
* Changed the initial default target layer to 1 (#395)
  
  Previously, the first generator command of the pipeline would default to create a new layer if the `--layer` option was not provided. This could lead to unexpected behaviour in several situation. The target layer is now layer 1. For subsequent generators, the existing behaviour of using the previous generator target layer as default remains.   

* Added `pagerotate` command, to rotate the page layout (including geometries) by 90 degrees (#404)
* Added `--keep` option to the `ldelete` command (to delete all layers but those specified) (#383)
* Providing a non-existent layer ID to any `--layer` parameter now generates a note (visible with `--verbose`) (#359, #382)

### Bug fixes

* Fixed an issue with the `random` command when using non-square area (#395)

### API changes

* Moved all CLI-related APIs from `vpype` to `vpype_cli` (#388)

  A number of CLI-related APIs remained in the `vpype` package for historical reasons. They are now located in the `vpype_cli` package for consistency and to allow for future extensions.

  * Moved the following decorators, classes, and functions from the `vpype` package to the `vpype_cli` package. Importing from `vpype` will now generate a deprecation warning:
    * `@block_processor`
    * `@generator`
    * `@global_processor`
    * `@layer_processor`
    * `@pass_state`
    * `AngleType`
    * `LayerType`
    * `LengthType`
    * `PageSizeType`
    * `multiple_to_layer_ids()`
    * `single_to_layer_id()`
  * Moved and renamed `vpype.VpypeState` to `vpype_cli.State`. Using the old name will generate a deprecation warning. 
  * Removed the following long-time deprecated aliases:
    * `vpype.Length` (alias to `vpype_cli.LengthType`) 
    * `vpype.VectorData` (alias to `vpype.Document`)
    * `vpype.convert()`(alias to `vpype.convert_length()`)
    * `vpype.convert_page_format()` (alias to `vpype.convert_page_size()`)
    * `vpype.PAGE_FORMATS` (alias to `vpype.PAGE_SIZES`)

* Added support for property substitution in Click type subclasses (#395)
  * Existing type classes (`AngleType`, `LengthType`, `PageSizeType`) now support property substitution.
  * Added `TextType` and `IntegerType` to be used instead of `str`, resp. `int`, when property substitution support is desired.
* Updated the block processor API (breaking change) (#395)
  
  Block processor commands (decorated with `@block_processor`) are no longer sub-classes of `BlockProcessor` (which has been removed). The are instead regular functions (like commands of other types) which take a `State` instance and a list of processors as first arguments.

* Added methods to `vpype_cli.State` to support expression and property substitution, deferred arguments/options evaluation and block processor implementations (#395, #397)
* `vpype.Document` and `vpype.LineCollection` have multiple, non-breaking additions to support metadata (in particular through the `vpype._MetadataMixin` mix-in class) (#359, #397)
* Renamed `vpype.Document.empty_copy()` to `vpype.Document.clone()` for coherence with `vpype.LineCollection` (the old name remains for backward compatibility) (#359, #380) 
* Added `vpype.read_svg_by_attribute()` to read SVG while sorting geometries by arbitrary attributes (#378)
* Added an argument to `vpype_cli.execute()` to pass global option such as `--verbose` (#378)

### Other changes

* Renamed the bundled config file to `vpype_config.toml` (#359)
* Pinned poetry-core to 1.0.8 to enable editable installs (#410)
* Changed dependencies to dataclasses (instead of attrs) and tomli (instead of toml) (#362)
* Removed dependency to click-plugin (#388)
* Improved documentation, in particular the [Fundamentals](https://vpype.readthedocs.io/en/latest/fundamentals.html) and [Cookbook](https://vpype.readthedocs.io/en/latest/cookbook.html) sections (#359, #363, #397)


## 1.8.1

Release date: 2022-01-13

### Security fix

* Updated Pillow to 9.0.0 due to vulnerabilities in previous versions (CVE-2022-22815, CVE-2022-22817, CVE-2022-22816)


## 1.8

Release date: 2021-11-25

### New features and improvements

* Added `lswap` command to swap the content of two layers (#300)
* Added `lreverse` command to reverse the order of paths within a layer (#300)
* Improved HPGL export (#253, #310, #316, #335)

  * Relative coordinates are now used by default to reduce file size. If absolute coordinates are needed, they a new `--absolute` option for the `write` command.
  * A homing command (as defined by the `final_pu_params` configuration parameter) is no longer emitted between layers.
* The viewer (`show` command) now catches interruptions from the terminal (ctrl-C) and closes itself (#321)
* The `read` command now accepts `-` as file path to read from the standard input (#322)

### Bug fixes

* Fixed issue with HPGL export where page size auto-detection would fail when using the default device from the config file (instead of specifying the device with `--device`) (#328)
* Fixed issue where the viewer would crash with empty layers (#339) 

### Other changes

* Updated to Shapely 1.8 (transition release toward 2.0) and fixed deprecation warnings (#325, #342)


## 1.7

Release date: 2021-06-10

**Important**: for a regular installation, *vpype* must now be installed/updated with the following command (see details below):
```
pip install -U vpype[all]
```

### New features and improvements

* Installing the viewer (`show` command) and its dependencies is now optional (#254)
  
  The `all` extra must now be provided to `pip` for a complete install:
  ```
  pip install -U vpype[all]  # the viewer is fully installed
  pip install -U vpype       # the viewer and its dependencies are NOT installed
  ```
  Forgoing the viewer considerably reduces the number of required dependencies and may be useful for embedded (e.g. Raspberry Pi) or server installs of *vpype*, when the `show` command is not necessary. Note that the Windows installer is not affected by this change.
* Added an optional, global optimization feature to `linesort` (#266, thanks to @tatarize)

  This feature is enabled by adding the `--two-opt` option. Since it considerably increases the processing time, it should primarily be used for special cases such as plotting the same file multiple times.

### Bug fixes

* Fixed broken Windows installer (#285)
* Fixed an issue where `read` would crash with empty `<polygon>` tags and similar degenerate geometries (#260)
* Fixed an issue where `linesimplify` would skip layers containing a single line (#280)
* Fixed an issue where floating point value could be generated for HPGL VS commands (#286)

### Other changes

* Updated to Click 8.0.1 (#282) 


## 1.6

Release date: 2021-03-10

### New features and improvements

* Added new `text` command  (#226, #227)
  
  This command renders text using Hershey fonts. It can create text blocks with wrapping, custom alignment, and optional justification. A set of Hershey fonts is included.

  **Notes**:
  * This feature was previously partially available via the [*vpype-text*](https://github.com/abey79/vpype-text) plug-in, which is now deprecated. The plug-in should no longer be used, and, if present, uninstalled.
  * The implementation of this feature as well as the set of Hershey font is based on the [axi project](https://github.com/fogleman/axi) -- thanks @fogleman!

* Added `squiggles` command for a "shaky hand" or "liquid-like" styling (#217)
* Added probabilistic mode to `lmove`, `lcopy`, and `ldelete` to enable various random coloring effects (#220)

### Bug fixes

* Fixed missing documentation for the `reverse` command (#217)

### API changes

* Added `vpype.FONT_NAMES`, `vpype.text_line`, and `vpype.text_block` for Hershey-font-based text rendering (#226, #227)

### Other changes

* Dropped support for Python 3.6 (#207)


## 1.5.1

Release date: 2021-02-19

### Bug fixes

* Fixed a shader compilation issue arising on some Windows configuration (#210)
* Fixed UI glitches when using both non-HiDPI and HiDPI (a.k.a Retina) monitors (#211)


## 1.5

Release date: 2021-02-16

**Note**: This is the last version of *vpype* to support Python 3.6.

### New features and improvements

* Viewer improvements:
  * Added rulers with dynamic scale to the display (can be optionally hidden) (#199)
  * Added metric and imperial unit system (in addition to pixels), used by the rulers and the mouse coordinates display (#199, #205)
  * Adjusted the size of the mouse coordinates text on Windows (#199)
  * Added support to adjust the scale of the UI via `~/.vpype.toml` (#203)
  
    This is achieved by adding the following lines to your `~/.vpype.toml` file:
    ```toml
    [viewer]
    ui_scale_factor = 1.5
    ```  
    A value of 1.5 may be useful on some Windows configurations where the default UI is very small.
  
### Bug fixes

* Fixed issue on Linux where `show` would revert to the classic viewer due to a `libX11` discovery issue (#206)

### API changes

* Renamed `vpype.CONFIG_MANAGER` in favour of `vpype.config_manager` (existing name kept for compatibility) (#202)


## 1.4

Release date: 2021-02-08

### New features and improvements

* Python 3.9.1 (or later) is finally supported and now is the recommended version (#115)
* Viewer improvements:
  * The viewer will now keep the page fitted to the window when resizing, until manually zoomed and/or panned (#193)
  * Significantly optimized launch and setting changes times (#184, #195)

### Bug fixes

* Various documentation fixes and improvements:
  * improved the `layout` command's help text
  * improved the cookbook section on using `GNU parallel` (#108)
  * fixed typos related to the `layout` command in the cookbook (#186, thanks to @f4nu)

### API changes

* Added support for a sidebar in the viewer (#194)


## 1.3

Release date: 2021-01-27

### New features and improvements

* Added new `layout` command (#168)
  
  This command automates the page layout process on a specified the page size by centering the geometries (with
  customizable horizontal and vertical alignment) and optionally fitting to specified margins. It intends to supersede
  `write`'s layout options (i.e. `--page-size` and `--center`) in more intuitive way. In particular this command
  acts on the pipeline rather than on the output file so its effect can be previewed with the `show` command.

* (Beta) Complete rewrite of the viewer underlying the `show` command (#163)
  * fully hardware-accelerated rendering engine
  * smooth zooming and panning, with touchpad and mouse support
  * preview mode with adjustable pen width and opacity
  * outline mode with optional colorful and point display
  * optional pen-up trajectories display
  * per-layer visibility control
  * interactively adjustable display settings
    
  **Note**: This new viewer is a beta feature and will evolve in future versions. Your feedback is welcome. The current, matplotlib-based viewer is still available using `show --classic`.

* Added support for arbitrary paper size to `write`'s HPGL output (configuration for the Calcomp Designmate included, check the documentation for details) (#178)
* Added large format paper sizes (A2, A1, A0) (#144)
* The `splitall` command will now filter out segments with identical end-points (#146)
* Minor loading time improvement (#133)

### Bug fixes

* Various documentation fixes (#170, #172, thanks to @theomega)

### API changes

* Added the new viewer engine and Qt-based GUI (#163)


## 1.2.1

Release date: 2020-12-26

### Hot fix

* Fixed systematic crash with `read` command due to bad dependency version (#140)


## 1.2

Release date: 2020-12-17

### New features and improvements

* A Windows installer is now available (#120)
* HPGL output: `--page-size` is no longer mandatory and `write` will try to infer which paper to use based on the current page size (#132)  
* Added `reverse` command (#129)

### Bug fixes

* Fixed crash for SVG with <desc> element (#127)
* Fixed an issue where output HPGL file could be empty (#132)


## 1.1
  
Release date: 2020-12-10

### New features and improvements
  
* Added `snap` command (#110)
* Invisible SVG elements are now discarded (#103)
* Add support for angle units (affects `rotate`, `skew`, and `arc` commands, `--radian` option is removed) (#111)

### Bug fixes
  
* Fixed installation issue on Windows ("Numpy sanity check RuntimeError") (#119)
* Fixed `write` to cap SVG width and height to a minimum of 1px (#102)
* Fixed grouping of `stat` command in `vpype --help`

### API changes
  
* Added `vpype_cli.execute()` to execute a vpype pipeline from Python (#104)
* Added `vpype.convert_angle()` and `vpype.AngleType` (#111)


## 1.0

Release date: 2020-11-29

* Initial release
