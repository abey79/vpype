.. _install:

============
Installation
============

This page explain how to install *vpype* for end-users. If you intend to develop on *vpype*, refer to the the :ref:`contributing` section.


macOS
=====

.. highlight:: bash

While macOS ships with a version of Python, this has been deprecated by Apple and may change in future version. Instead, you should install Python (3.9.1 or newer recommended, 3.6 minimum), either from `MacPorts <https://www.macports.org>`_ or from `Homebrew <https://brew.sh>`_.

Use the following commands for Homebrew::

  $ brew install python@3.9

And for MacPorts::

  $ sudo port install python39

Then, the preferred way to install *vpype* is in a dedicated `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_. Follow these steps to do so::

  $ python3 -m venv vpype_venv      # create a new virtual environment
  $ source vpype_venv/bin/activate  # activate the newly created virtual environment
  $ pip install --upgrade pip
  $ pip install vpype

You should now be able to run *vpype*::

  $ vpype --help

Each time a new terminal window is opened, the virtual environment must be activated using::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help


Windows
=======

.. highlight:: bat

A Windows installer is available `here <https://github.com/abey79/vpype/releases>`__. Although this installation method is easier, it does not allow plug-ins to be installed. If plug-ins are required, a manual installation is recommended.

First, Python must be installed. Python 3.9 is recommended, although it is also compatible with Python 3.6 and later. The official Python distribution for Windows can be downloaded `here <https://www.python.org/downloads/>`__.

After installing Python, launch a terminal (by typing ``cmd`` in the Start menu) and enter the following command to install *vpype*::

  > pip install vpype

You should then be able to run *vpype*::

  > vpype --help

Installing in a virtual environment
-----------------------------------

`Virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ are used to isolate the dependencies of one project from the the rest of your Python installation. Unless your Python installation is essentially dedicated to *vpype*, installing it in a virtual environment rather than in the global scope is preferable to avoid interferences.

To create a virtual environment for your *vpype* installation, launch the ``cmd`` terminal and enter the following commands::

  > python -m venv vpype_venv

This will create a ``vpype_venv`` directory which will contain everything needed to run *vpype*. Before using an environment, you need to activate it::

  > vpype_venv\Scripts\activate.bat

You will need to activate your virtual environment each time you launch a new  terminal. With your virtual environment activated, type the following command to install *vpype*::

  > pip install vpype

You should now be able to use *vpype*. Type this for a list of command::

  > vpype --help

This command should open a window showing a circle::

  > vpype circle 0 0 10cm show

If you can see it, your installation is up and running!


Linux
=====

.. highlight:: bash

*vpype* requires Python 3.6 or later. On Debian/ubuntu flavored installation, installing Python is a matter of::

  $ sudo apt-get install python3 python3-pip

The preferred way to install *vpype* is in a dedicated `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_. Follow these steps to do so::

  $ python3 -m venv vpype_venv      # create a new virtual environment
  $ source vpype_venv/bin/activate  # activate the newly created virtual environment
  $ pip install --upgrade pip
  $ pip install vpype

You should now be able to run *vpype*::

  $ vpype --help

Each time a new terminal window is opened, the virtual environment must be activated using::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help


Raspberry Pi
============

Installation on the Raspberry Pi is no longer supported. Expert users may succeed with `pip install vpype` provided that a suitable version of the PySide2 package is available. Also, new viewer requires OpenGL 3.3, which the Raspberry Pi does not support. The classic viewer should work correctly:

  $ vpype [...] show --classic