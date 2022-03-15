.. currentmodule:: vpype

.. _plugins:

========
Plug-ins
========

.. _plugins_why:

Why?
====

Thanks to the CLI library which underlies *vpype* (`Click <https://click.palletsprojects.com>`_), writing plug-ins is easy and makes it a compelling option for your next plotter project. Plug-ins directly benefit from *vpype*'s facilities, such as SVG export, line optimization and sorting, scaling and pagination, etc. Plug-ins also benefit from the Click-inherited facilities to easily create compelling CLI interfaces to parametrize your plug-in.

Here are a few existing plug-ins to illustrate the possibilities:

* `vpype-gcode <https://github.com/plottertools/vpype-gcode>`__: flexible export to gcode or any other text-based format
* `vpype-embroidery <https://github.com/EmbroidePy/vpype-embroidery>`__: convert to/from common embroidery file formats
* `vpype-dxf <https://github.com/tatarize/vpype-dxf>`__: read from DXF
* `vpype-vectrace <https://github.com/tatarize/vpype-vectrace>`__: trace from bitmap images
* `occult <https://github.com/LoicGoulefert/occult>`__: perform hidden line removal with closed geometry
* `deduplicate <https://github.com/LoicGoulefert/deduplicate>`__: remove overlapping lines

  .. image:: https://raw.githubusercontent.com/LoicGoulefert/occult/master/img/example8.png
     :height: 400px

* `vpype-flow-imager <https://github.com/serycjon/vpype-flow-imager>`__: convert image to flow field line art

  .. image:: https://raw.githubusercontent.com/serycjon/vpype-flow-imager/master/examples/coffee.jpg
     :width: 300px
  .. image:: https://raw.githubusercontent.com/serycjon/vpype-flow-imager/master/examples/coffee_out.png
     :width: 300px

* `vpype-pixelart <https://github.com/abey79/vpype-pixelart>`__: easy pixel art plotting

  .. image:: https://i.redd.it/g1nv7tf20aw11.png
     :width: 400px

  .. image:: https://i.imgur.com/dAPqFGV.jpg
     :width: 400px

  (original art by Reddit user `u/\_NoMansDream <https://www.reddit.com/user/_NoMansDream/>`_)

- `hatched <https://github.com/abey79/hatched>`__: convert images to hatched patterns

  .. image:: https://i.imgur.com/QLlBpNU.png
     :width: 300px

  .. image:: https://i.imgur.com/fRIrPV2.jpg
     :width: 300px


.. _plugins_how:

How?
====

.. highlight:: bash

The easiest way to start a plug-in project is to use the `Cookiecutter <https://cookiecutter.readthedocs.io>`_ template for *vpype* plug-ins. You will first need to install ``cookiecutter`` command (see the website for more info). Then, run the following command::

  $ cookiecutter gh:abey79/cookiecutter-vpype-plugin

Cookiecutter will ask you a few questions and create a project structure automatically. To make it operational, the plug-in and its dependencies (including *vpype* itself) must be installed in a local virtual environment::

  $ cd my-vpype-plugin/
  $ python3 -m venv venv
  $ source venv/bin/activate
  $ pip install --upgrade pip
  $ pip install --editable .

Note the use of the ``--editable`` flag when installing the plug-in. With this flag, the actual code in the plug-in project is used for the plug-in, which means you can freely edit the source of the plug-in and it is automatically used the next time *vpype* is run.

Let's check that that everything works as expected::

  $ vpype --help
  Usage: vpype [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

  Options:
    -v, --verbose
    -I, --include PATH  Load commands from a command file.
    --help              Show this message and exit.

  Commands:

    ...

    Plugins:
      my-vpype-plugin  Insert documentation here.

    ...

The cookiecutter project includes a single :ref:`generator <fundamentals_generators>` command with the :func:`@vpype_cli.generator <vpype_cli.generator>` decorator:

.. code-block:: python

  import click
  import vpype as vp
  import vpype_cli

  @click.command()
  @vpype_cli.generator
  def my_vpype_plugin():
      """Insert documentation here.
      """
      lc = vp.LineCollection()
      return lc

  my_vpype_plugin.help_group = "Plugins"

Generator commands must return a :py:class:`vpype.LineCollection` instance. Plug-in can also contain :ref:`layer processor <fundamentals_layer_processors>` or :ref:`global processor <fundamentals_global_processors>` command, respectively using the :func:`@vpype_cli.layer_processor <vpype_cli.layer_processor>` and :py:func:`@vpype_cli.global_processor <vpype_cli.global_processor>` decorators. Check the API reference for more information.


.. _plugins_help:

Getting help
============

This being a rather young project, documentation may be missing and/or rough around the edges. The author is available for support on `Drawingbots <https://drawingbots.net>`_'s `Discord server <https://discordapp.com/invite/XHP3dBg>`_.
