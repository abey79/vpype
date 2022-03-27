.. _install:

============
Installation
============

This page explain how to install *vpype* for end-users. If you intend to develop on *vpype*, refer to the the :ref:`contributing` section.


.. note::

  The recommended Python version is 3.10.2 or later (except for macOS/M1 computer, for which Python 3.9 is recommended). *vpype* is also compatible with Python 3.8 and 3.9.

..
  Overview
  ========

  This table provides an overview of the available methods to install *vpype*. The recommended method is using `pipx`_.

  .. csv-table::
     :header: Installation Method, macOS, Windows, Linux, Note
     :widths: 12, 5, 5, 5, 18

     `pipx`_, ✅ , ✅, ✅, "| ✅ recommended method
     | ⚠️ see instruction for macOS/M1"
     `pip`_ (global installation), ✅, ✅, ✅, ⚠️⚠️⚠️ **strongly discouraged**
     `pip`_ (virtual environment), ✅, ✅, ✅, a virtual environment must be manually created *and* activated
     installer, 🚫, ✅, 🚫, does not support plug-ins
     `MacPorts`_, ✅️, 🚫, 🚫, ⚠️ plug-ins must be installed globally (not recommended)

  Installing Python and a Python-based package can be overwhelming for new users. The following glossary shortly defines a few of the key terms and notions.

  Python interpreter
    Any Python-based package needs a Python interpreter to be executed. A major version of the Python interpreter is released every year. The current one is the Python 3.10 series. In general, using the latest version is recommended but using an older version is sometime necessary. For example, *vpype* requires Python 3.9 to run on macOS/M1 computers.

  `pip`_
    `pip`_ is the fundamental tool to download and install publicly-available packages like *vpype*. These package are stored in the `Python Package Archive <PyPI>`_ where they can be found by pip. pip automatically download and install all the dependencies required by the package.

  Global installation
    By default, pip installs packages globally, next to the Python interpreter. Such package become available to all users and software on the computer. Although doing so may sound reasonable, it is in general strongly discouraged because of the very likely risk of conflicts when different packages relies on different version of the same dependencies.

  `Virtual Environments <venv>`_
    To avoid the conflict issue, packages and their dependencies, a `virtual environments <venv>`_ may be created. They behave like isolated, self-contained directory which contains both the Python interpreter, the desired package, and its dependencies. Multiple virtual environments can be used for different tasks, avoiding all risks of conflicts. When using `pip`_, packages will be installed in a given virtual environment *if (and only if)* said virtual environment was previously activated (activating a virtual environment makes its content available to the current terminal session). Managing and using virtual environments can either be done manually (using the `venv`_ standard Python package), or can be done automatically using some high-level tool.

  `pipx`_
    `pipx`_ is such a high-level tool and is made to install Python-based CLI software such as *vpype*. Specifically, it automates two important tasks: (1) it automatically creates and manages a virtual environment for every software installed with it and (2) it ensures that the installed software is in the path and thus available in terminal windows.

  `MacPorts`_
    `MacPorts`_ is a package manager dedicated to the installation of various open-source software and libraries on the Mac platform. It is similar to the packages manager typically found in Linux distributions.


macOS
=====

.. caution::

   **macOS/M1 note**: Due to the restricted availability of an ARM-compatible PySide2 library, installing *vpype* on a macOS/M1 computers requires the specific steps described bellow. Using alternative ways to install Python and *vpype* may work, but typically don't and are thus discouraged.

.. highlight:: bash

`MacPorts`_ is the recommended way to install the Python interpreter on macOS.

Following the `installation instructions <https://www.macports.org/install.php>`__ to install MacPorts. Then, make sure its port database is up-to-date::

  $ sudo port selfupdate
  $ sudo port upgrade outdated


Installing using the MacPorts port
----------------------------------

.. note::

   Although this is the easiest way to install *vpype*, it is discouraged when using :ref:`plug-ins <plugins>` because they would have to be globally installed.

Installing *vpype* using the port can be done with the following command::

  $ sudo port install vpype

This installation method works for both Intel- and M1-based Macs.


Installing using pipx (Apple silicon/M1)
----------------------------------------

Installing *vpype* on Macs with Apple Silicon requires specific steps because some its dependencies are not yet fully supported on this architecture. Using `pipx`_ is the recommended method when using plug-ins.

First, install the required ports using MacPorts::

  $ sudo port install python39 py39-shapely py39-scipy py39-numpy py39-pyside2

Then, install pipx::

  $ sudo port install pipx +python39
  $ pipx ensurepath

The second command above ensures that both pipx and the software it will install are available the terminal. You may need to close and re-open the terminal window for this to take effect.

Finally, install *vpype*::

  $ pipx install "vpype[all]" --system-site-packages

Note the use of the ``--system-site-packages`` option. This is important because because *vpype* relies the version of PySide2 that was installed earlier with MacPort.

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  $ vpype --version
  vpype 1.9.0
  $ vpype random show


Installing using pipx (Intel)
-----------------------------

.. note::

   The instructions for Apple silicon/M1 Macs also apply, but since dependencies have better support for Intel-based Macs, some steps may be simplified.

First, install pipx::

  $ sudo port install pipx
  $ pipx ensurepath
  
The second command above ensures that both pipx and the software it will install are available the terminal. You may need to close and re-open the terminal window for this to take effect.

Then, install *vpype*::

  $ pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  $ vpype --version
  vpype 1.9.0
  $ vpype random show


Installing using pipx and the official Python distribution
----------------------------------------------------------

For Intel-based Macs, the official Python distribution may be used as an alternative to MacPorts. It can be downloaded from the `official Python website <https://www.python.org/downloads/>`_.

After running the Python installer, install pipx with the following command::

  $ sudo python3 -m pip install pipx
  $ pipx ensurepath

The second command above ensures that both pipx and the software it will install are available the terminal. You may need to close and re-open the terminal window for this to take effect.

Then, install *vpype*::

  $ pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  $ vpype --version
  vpype 1.9.0
  $ vpype random show


Windows
=======

.. highlight:: bat

Installing using the installer
------------------------------

A Windows installer for *vpype* is `available here <https://github.com/abey79/vpype/releases>`__. Although this installation method is the easiest, it **does not** allow plug-ins to be installed. If plug-ins are required, installing using pipx is recommended.

Installing using pipx
---------------------

First, Python must be installed. Python 3.10 is recommended, although *vpype* it is also compatible with Python 3.8 and later. The official Python distribution for Windows can be `downloaded here <https://www.python.org/downloads/>`__ or installed from the `App Store <https://www.microsoft.com/en-us/p/python-310/9pjpw5ldxlz5>`_. When installing Python, make sure you enable adding Python to the path.

First, install pipx::

  > python -m pip install --user pipx
  > pipx ensurepath

In the first command, replace ``python`` by ``python3`` if you installed Python from the App Store. The second command above ensures that both pipx and the software it will install are available the terminal. You may need to close and re-open the terminal for this to take effect.

Then, install *vpype*::

  > pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  > vpype --version
  vpype 1.9.0
  > vpype random show

Linux
=====

.. highlight:: bash

First, install `pipx`_ with your system's package manager. On Debian/ubuntu flavored installation, this is typically done as follows::

  $ sudo apt-get install pipx

Then run the following command to ensure your path variable is properly set::

  $ pipx ensurepath

You may need to close and re-open the terminal window for this to take effect.

Finally, install *vpype*::

  $ pipx install "vpype[all]"

*vpype* should now be installed and ready to use. You may check that it is fully functional by checking its version and displaying some random lines::

  $ vpype --version
  vpype 1.9.0
  $ vpype random show



Raspberry Pi
============

Full installation including the viewer on the Raspberry Pi is no longer supported. Expert users may succeed with ``pip install vpype[all]`` provided that a suitable version of the PySide2 package is available. Also, the new viewer requires OpenGL 3.3, which the Raspberry Pi does not support. The classic viewer should work correctly::

  $ vpype [...] show --classic

Installing the CLI-only version described in the next section is easier and should be favored whenever possible. Here are the recommended steps to do so.

Some packages and their dependencies are easier to install at the system level::

  $ sudo apt-get install python3-shapely python3-numpy python3-scipy

Then, install pipx::

  $ sudo apt-get install pipx
  $ pipx ensurepath

Finally, install and run *vpype*::

  $ pipx install vpype
  $ vpype --version
  vpype 1.9.0


CLI-only install
================

For special cases where the :ref:`cmd_show` is not needed and dependencies such as matplotlib, PySide2, or ModernGL are difficult to install, a CLI-only version of *vpype* can be installed using this command::

  $ pipx install vpype

Note the missing ``[all]`` compared the instructions above.


.. _pip: https://pip.pypa.io/en/stable
.. _pipx: https://pypa.github.io/pipx
.. _MacPorts: https://www.macports.org
.. _PyPI: https://pypi.org
.. _venv: https://docs.python.org/3/library/venv.html