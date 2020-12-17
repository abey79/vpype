# Change log

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
