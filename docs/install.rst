.. _install:

============
Installation
============

This page explain how to install *vpype* for end-users. If you intend to develop on *vpype*, refer to the the :ref:`contributing` section.


.. note::

  The recommended Python version is 3.13. *vpype* is also compatible with Python 3.11 and 3.12.

.. warning::

  *vpype* is not yet compatible with Python 3.13.


macOS
=====

.. highlight:: bash


Installing Python
-----------------

The official installer is the recommended way to install Python on your computer. It can be downloaded `here <https://www.python.org/downloads/>`__.

.. caution::

  When install Python, make sure to select version that is compatible with *vpype*. See the :doc:`top of this page <install>` for more information.


You can  ensure that the installed Python interpreter is properly installed by running this command::

  python3 --version

It should produce an output similar to::

  Python 3.13.2

The version number should match the installer you used.

Note that installing Python from `Homebrew <https://brew.sh>`__ or `MacPorts`_ is possible as well.


Installing pipx
---------------

`pipx`_ is a tool that allows you to install Python applications in isolated environments. It is the recommended way to install *vpype* on macOS. It can be installed with the following commands::

  python3 -m pip install pipx
  python3 -m pipx ensurepath

After this, restart your terminal and ensure that pipx is properly installed by running this command::

  pipx --version

It should print out the current version of pipx without error::

  1.2.0


Installing *vpype*
------------------

Once pipx is properly installed, you can install *vpype* with the following command::

  pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version or displaying some random lines::

  vpype --version
  vpype random show


Windows
=======

.. highlight:: bat

Installing using the installer
------------------------------

A Windows installer for *vpype* is `available here <https://github.com/abey79/vpype/releases>`__. Although this installation method is the easiest, it **does not** allow :doc:`plug-ins <plugins>` to be installed. If plug-ins are required, installing using pipx is recommended.

Installing using pipx
---------------------

First, install Python. The official Python distribution for Windows can be `downloaded here <https://www.python.org/downloads/>`__ or installed from the `App Store <https://www.microsoft.com/en-us/p/python-310/9pjpw5ldxlz5>`_. When installing Python, make sure you enable adding Python to the path.

.. caution::

  When install Python, make sure to select version that is compatible with *vpype*. See the :doc:`top of this page <install>` for more information.

Then, install pipx::

  python -m pip install --user pipx
  pipx ensurepath

In the first command, replace ``python`` by ``python3`` if you installed Python from the App Store. The second command above ensures that both pipx and the software it will install are available the terminal. You may need to close and re-open the terminal for this to take effect.

Finally, install *vpype*::

  pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  vpype --version
  vpype random show

Linux
=====

.. highlight:: bash

First, install `pipx`_ with your system's package manager. On Debian/Ubuntu flavored installation, this is typically done as follows::

  sudo apt-get install pipx

Then run the following command to ensure your path variable is properly set::

  pipx ensurepath

You may need to close and re-open the terminal window for this to take effect.

Finally, install *vpype*::

  pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  vpype --version
  vpype random show


Raspberry Pi
============

Full installation including the viewer on the Raspberry Pi is no longer supported. Expert users may succeed with ``pipx install "vpype[all]"``. Also, the new viewer requires OpenGL 3.3, which the Raspberry Pi does not support. The classic viewer should work correctly::

  vpype [...] show --classic

Installing the CLI-only version described in the next section is easier and should be favored whenever possible. Here are the recommended steps to do so.

Some packages and their dependencies are easier to install at the system level::

  sudo apt-get install python3-shapely python3-numpy python3-scipy

Then, install pipx::

  sudo apt-get install pipx
  pipx ensurepath

Finally, install and run *vpype*::

  pipx install vpype
  vpype --version


CLI-only install
================

For special cases where the :ref:`cmd_show` is not needed and dependencies such as matplotlib, PySide6, or ModernGL are difficult to install, a CLI-only version of *vpype* can be installed using this command::

  pipx install vpype

Note the missing ``[all]`` compared the instructions above.


.. _pip: https://pip.pypa.io/en/stable
.. _pipx: https://pypa.github.io/pipx
.. _MacPorts: https://www.macports.org
.. _PyPI: https://pypi.org
.. _venv: https://docs.python.org/3/library/venv.html