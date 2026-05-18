.. _install:

============
Installation
============

This page explain how to install *vpype* for end-users. If you intend to develop on *vpype*, refer to the the :ref:`contributing` section.


.. note::

  *vpype* is compatible with Python 3.11, 3.12, and 3.13.

The recommended way to install *vpype* is with `uv`_, a fast Python package and project manager that can also manage Python installations and install standalone tools (similar to ``pipx``). With ``uv tool install``, you do not need to install Python yourself: ``uv`` will download a suitable pre-built Python interpreter automatically and isolate *vpype* in its own environment.


Installing uv
=============

Follow the `official uv installation instructions <https://docs.astral.sh/uv/getting-started/installation/>`_ for your platform. The most common commands are reproduced below for convenience, but please refer to the official documentation for the most up-to-date information.

.. highlight:: bash

On macOS and Linux::

  curl -LsSf https://astral.sh/uv/install.sh | sh

.. highlight:: powershell

On Windows (PowerShell)::

  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

After installing ``uv``, restart your terminal and confirm it is available::

  uv --version


Installing *vpype*
==================

Once ``uv`` is installed, use ``uv tool install`` to install *vpype*. The package name is ``vpype[all]`` (the ``[all]`` extra pulls in the viewer dependencies: matplotlib, PySide6, and ModernGL).

.. caution::

  In zsh and bash (the default shells on macOS and Linux), the square brackets in ``vpype[all]`` are interpreted as shell glob characters and **must be quoted**. On Windows ``cmd.exe`` they are not special, but on PowerShell they are — so quoting everywhere on Windows is the safer default.

.. important::

  The commands below pass ``--python 3.13`` explicitly. Without it, ``uv`` will pick the newest Python interpreter available, and at least one of the viewer dependencies (ModernGL) does not yet publish wheels for Python 3.14, which causes the install to fail trying to build from source. Python 3.13 is the latest version for which all viewer dependencies ship pre-built wheels.


macOS and Linux (bash, zsh)
---------------------------

.. highlight:: bash

::

  uv tool install --python 3.13 "vpype[all]"


Windows (cmd.exe)
-----------------

.. highlight:: bat

::

  uv tool install --python 3.13 vpype[all]


Windows (PowerShell)
--------------------

.. highlight:: powershell

::

  uv tool install --python 3.13 "vpype[all]"


Verifying the installation
==========================

.. highlight:: bash

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version or displaying some random lines::

  vpype --version
  vpype random show


Why ``--python 3.13``?
======================

By default, ``uv tool install`` selects the most recent Python interpreter compatible with *vpype*'s ``requires-python`` constraint and downloads a managed, pre-built standalone Python build if needed. As long as every dependency publishes wheels for that interpreter, the install completes without any compilation.

The problem is that wheel coverage for the very latest Python release tends to lag. At the time of writing, ModernGL (a viewer dependency) does not yet ship wheels for Python 3.14, so letting ``uv`` pick 3.14 results in a build-from-source attempt that fails on most machines. Pinning ``--python 3.13`` sidesteps this by targeting the latest interpreter for which all viewer dependencies have pre-built wheels.

Once ModernGL (and any other lagging dependency) publishes 3.14 wheels, you can drop the flag — or bump it to a newer version — and ``uv`` will resolve normally.


Raspberry Pi
============

.. highlight:: bash

Full installation including the viewer on the Raspberry Pi is no longer supported. Expert users may succeed with ``uv tool install --python 3.13 "vpype[all]"``. Also, the new viewer requires OpenGL 3.3, which the Raspberry Pi does not support. The classic viewer should work correctly::

  vpype [...] show --classic

Installing the CLI-only version described in the next section is easier and should be favored whenever possible.


CLI-only install
================

.. highlight:: bash

For special cases where the :ref:`cmd_show` is not needed and dependencies such as matplotlib, PySide6, or ModernGL are difficult to install, a CLI-only version of *vpype* can be installed using this command::

  uv tool install vpype

Note the missing ``[all]`` compared the instructions above. Since there are no square brackets, no quoting is required on any shell.


.. _pip: https://pip.pypa.io/en/stable
.. _uv: https://docs.astral.sh/uv/
.. _MacPorts: https://www.macports.org
.. _PyPI: https://pypi.org
.. _venv: https://docs.python.org/3/library/venv.html
