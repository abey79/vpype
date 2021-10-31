# Change log

#### 1.8 (UNRELEASED)

New features and improvements:
* Added `lswap` command to swap the content of two layers (#300)
* Added `lreverse` command to reverse the order of paths within a layer (#300)
* Improved HPGL export (#253, #310, #316)

  * Relative coordinates are now used by default to reduce file size. If absolute coordinates are needed, they a new `--absolute` option for the `write` command.
  * A homing command (as defined by the `final_pu_params` configuration parameter) is no longer emitted between layers.
* The viewer (`show` command) now catches interruptions from the terminal (ctrl-C) and closes itself (#321)
* The `read` command now accepts `-` as file path to read from the standard input (#322)

Bug fixes:
* Fixed issue with HPGL export where page size auto-detection would fail when using the default device from the config file (instead of specifying the device with `--device`) (#XXX)


#### 1.7 (2021-06-10)

**Important**: for a regular installation, *vpype* must now be installed/updated with the following command (see details below):
```
pip install -U vpype[all]
```

New features and improvements:
* Installing the viewer (`show` command) and its dependencies is now optional (#254)
  
  The `all` extra must now be provided to `pip` for a complete install:
  ```
  pip install -U vpype[all]  # the viewer is fully installed
  pip install -U vpype       # the viewer and its dependencies are NOT installed
  ```
  Forgoing the viewer considerably reduces the number of required dependencies and may be useful for embedded (e.g. Raspberry Pi) or server installs of *vpype*, when the `show` command is not necessary. Note that the Windows installer is not affected by this change.
* Added an optional, global optimization feature to `linesort` (#266, thanks to @tatarize)

  This feature is enabled by adding the `--two-opt` option. Since it considerably increases the processing time, it should primarily be used for special cases such as plotting the same file multiple times.

Bug fixes:
* Fixed broken Windows installer (#285)
* Fixed an issue where `read` would crash with empty `<polygon>` tags and similar degenerate geometries (#260)
* Fixed an issue where `linesimplify` would skip layers containing a single line (#280)
* Fixed an issue where floating point value could be generated for HPGL VS commands (#286)

Other changes:
* Updated to Click 8.0.1 (#282) 


#### 1.6 (2021-03-10)

New features and improvements:
* Added new `text` command  (#226, #227)
  
  This command renders text using Hershey fonts. It can create text blocks with wrapping, custom alignment, and optional justification. A set of Hershey fonts is included.

  **Notes**:
  * This feature was previously partially available via the [*vpype-text*](https://github.com/abey79/vpype-text) plug-in, which is now deprecated. The plug-in should no longer be used, and, if present, uninstalled.
  * The implementation of this feature as well as the set of Hershey font is based on the [axi project](https://github.com/fogleman/axi) -- thanks @fogleman!

* Added `squiggles` command for a "shaky hand" or "liquid-like" styling (#217)
* Added probabilistic mode to `lmove`, `lcopy`, and `ldelete` to enable various random coloring effects (#220)

Bug fixes:
* Fixed missing documentation for the `reverse` command (#217)

API changes:
* Added `vpype.FONT_NAMES`, `vpype.text_line`, and `vpype.text_block` for Hershey-font-based text rendering (#226, #227)


Other changes:
* Dropped support for Python 3.6 (#207)


#### 1.5.1 (2021-02-19)

Bug fixes:
* Fixed a shader compilation issue arising on some Windows configuration (#210)
* Fixed UI glitches when using both non-HiDPI and HiDPI (a.k.a Retina) monitors (#211)


#### 1.5 (2021-02-16)

**Note**: This is the last version of *vpype* to support Python 3.6.

New features and improvements:
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
  
Bug fixes:
* Fixed issue on Linux where `show` would revert to the classic viewer due to a `libX11` discovery issue (#206)

API changes:
* Renamed `vpype.CONFIG_MANAGER` in favour of `vpype.config_manager` (existing name kept for compatibility) (#202)


#### 1.4 (2021-02-08)

New features and improvements:
* Python 3.9.1 (or later) is finally supported and now is the recommended version (#115)
* Viewer improvements:
  * The viewer will now keep the page fitted to the window when resizing, until manually zoomed and/or panned (#193)
  * Significantly optimized launch and setting changes times (#184, #195)

Bug fixes:
* Various documentation fixes and improvements:
  * improved the `layout` command's help text
  * improved the cookbook section on using `GNU parallel` (#108)
  * fixed typos related to the `layout` command in the cookbook (#186, thanks to @f4nu)

API changes:
* Added support for a sidebar in the viewer (#194)


#### 1.3 (2021-01-27)

New features and improvements:
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

Bug fixes:
* Various documentation fixes (#170, #172, thanks to @theomega)

API changes:
* Added the new viewer engine and Qt-based GUI (#163)


#### 1.2.1 (2020-12-26)

Hot fix:
* Fixed systematic crash with `read` command due to bad dependency version (#140)


#### 1.2 (2020-12-17)

New features and improvements:
* A Windows installer is now available (#120)
* HPGL output: `--page-size` is no longer mandatory and `write` will try to infer which paper to use based on the current page size (#132)  
* Added `reverse` command (#129)

Bug fixes:
* Fixed crash for SVG with <desc> element (#127)
* Fixed an issue where output HPGL file could be empty (#132)


#### 1.1 (2020-12-10)

New features and improvements:
* Added `snap` command (#110)
* Invisible SVG elements are now discarded (#103)
* Add support for angle units (affects `rotate`, `skew`, and `arc` commands, `--radian` option is removed) (#111)

Bug fixes:
* Fixed installation issue on Windows ("Numpy sanity check RuntimeError") (#119)
* Fixed `write` to cap SVG width and height to a minimum of 1px (#102)
* Fixed grouping of `stat` command in `vpype --help`

API changes:
* Added `vpype_cli.execute()` to execute a vpype pipeline from Python (#104)
* Added `vpype.convert_angle()` and `vpype.AngleType` (#111)


#### 1.0 (2020-11-29)

* Initial release
