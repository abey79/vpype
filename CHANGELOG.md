# Change log

#### 1.5 (UNRELEASED)

...

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
