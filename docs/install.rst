.. _install:

============
Installation
============

This page explain how to install *vpype* for end-users. If you intend to develop on *vpype*, refer to the the :ref:`contributing` section.


macOS
=====

.. highlight:: bash

While macOS ships with a version of Python, this has been deprecated by Apple and may change in future version. Instead, you should install Python (preferably 3.8, minimum 3.6), either from `MacPorts <https://www.macports.org>`_ or from `Homebrew <https://brew.sh>`_.

Use the following commands for Homebrew::

  $ brew install python

And for MacPorts::

  $ sudo port install python38

Then, the preferred way to install *vpype* is in a dedicated `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_. Follow these steps to do so::

  $ python3 -m venv vpype_venv      # create a new virtual environment
  $ source vpype_venv/bin/activate  # activate the newly created virtual environment
  $ pip install --upgrade pip
  $ pip install git+https://github.com/abey79/vpype.git#egg=vpype

You should now be able to run *vpype*::

  $ vpype --help

Each time a new terminal window is opened, the virtual environment must be activated using::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help


Windows
=======

.. highlight:: bat

*vpype* being a young, actively developed project, an installer is not yet available, which means that a few steps are required for the installation.

Installing Python and git
-------------------------

*vpype* uses `Python <https://www.python.org/>`_ and its source accessible with `git <https://git-scm.com/>`_, so both of these software must be installed:

* `Official Python installer <https://www.python.org/downloads/windows/>`_ (version 3.8 recommended, 3.6 minimum)
* `Official git installer <https://git-scm.com/download/win>`_


Downloading Shapely
-------------------

*vpype* relies on a library named `Shapely <https://shapely.readthedocs.io>`_ which needs to be manually downloaded. You can
find it `here <https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely>`_ (courtesy of the
`Unofficial Windows Binaries for Python Extension Packages <https://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ archive).
Download the version that corresponds to your Python installation and architecture (32bit vs. 64bit). In most case, it
should be ``*‑cp38‑cp38‑win_amd64.whl`` for Python 3.8 and a non-ancient computer.


Create a virtual environment
----------------------------

`Virtual environment <https://docs.python.org/3/tutorial/venv.html>`_ are used to isolate the dependencies of one project from the others'. It is considered best practice to always use them as opposed to install Python libraries and tools in the global scope. To create a virtual environment for your *vpype* installation, launch the ``cmd`` terminal and enter the following commands::

  > python -m venv vpype_venv

This will create a ``vpype_venv`` directory which will contain everything needed to run *vpype*. Before using an environment, you need to activate it::

  > vpype_venv\Scripts\activate.bat

You will need to activate your virtual environment each time you launch a new  terminal.

Install everything and run *vpype*
----------------------------------

With your virtual environment activated, follow these steps to install everything.

If you are using an older version of Python (3.6 or 3.7, upgrade your version of ``pip``)::

  > pip install --upgrade pip

Install Shapely using the file you downloaded earlier::

  > pip install Shapely-1.7.0-cp38-cp38-win_amd64.whl

Finally, install *vpype*::

  > pip install git+https://github.com/abey79/vpype.git#egg=vpype

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
  $ pip install git+https://github.com/abey79/vpype.git#egg=vpype

You should now be able to run *vpype*::

  $ vpype --help

Each time a new terminal window is opened, the virtual environment must be activated using::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help


Raspberry Pi
============

.. highlight:: bash

Installing *vpype* on Raspbian is similar to Linux, but a number of libraries must be installed beforehand::

  $ sudo apt-get install git python3-shapely python3-dev

Also, the following command must be added to the ``~/.bashrc`` file for *vpype* to execute correctly::

  export LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libatomic.so.1
