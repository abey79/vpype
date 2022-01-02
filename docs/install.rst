.. _install:

============
Installation
============

This page explain how to install *vpype* for end-users. If you intend to develop on *vpype*, refer to the the :ref:`contributing` section.

.. caution::

    *vpype* is currently **not compatible with Python 3.10**. The recommended version is Python 3.9.9 (or later in the 3.9 series). *vpype* is
    also compatible with Python 3.8 and 3.7.

.. note::

   The preferred way to install *vpype* is in a dedicated `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_. The present installation instructions always include this step.


macOS (Apple Silicon/M1)
========================

.. highlight:: bash

Installing *vpype* on Macs with Apple Silicon is possible but requires specific steps because some its dependencies are not yet fully supported on this architecture. As a result, the Python interpreter *must* be installed from `MacPorts <https://www.macports.org>`_.

After `installing MacPorts <https://www.macports.org/install.php>`_, make sure its port database is up-to-date::

  $ sudo port selfupdate
  $ sudo port upgrade outdated

Then, install the required ports::

  $ sudo port install python39 py39-shapely py39-scipy py39-numpy py39-pyside2

Optionally, you may make Python 3.9 the default interpreter::

  $ sudo port select --set python python39

Then, create the virtual environment::

  $ /opt/local/bin/python3.9 -m venv vpype_venv --system-site-packages

A virtual environment named ``vpype_venv`` will be created in the current directory. There are two import points to note in the command above.
First, we use a full path (``/opt/local/bin/python3.9``) to ascertain that the virtual environment will use the right Python interpreter (i.e. MacPorts'). Second, we allow the virtual environment to use the global environment's packages (``--system-site-packages``). This is important because *vpype* needs MacPorts' version of PySide2 (``pip`` is unable to install PySide2 on Apple Silicon hardware).

Now that the virtual environment is created, it may be activated::

  $ source vpype_venv/bin/activate

Finally, *vpype* may be installed (note the prompt now reflecting the activated virtual environment)::

  (vpype_venv) $ pip install "vpype[all]"

You can test that *vpype* is fully functional by checking its version and displaying some random lines::

  (vpype_venv) $ vpype --version
  vpype 1.8.0
  (vpype_venv) $ vpype random show

Since *vpype* is installed within a virtual environment, it must be activated each time a new terminal window is opened::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed without activating the virtual environment by using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help


macOS (Intel)
=============

The instructions above also apply but, since dependencies have better support for Intel-based Macs, some steps may be simplified.

Firstly, the `official Python distribution <https://www.python.org/downloads/>`_ may be used instead of MacPorts' (again, install Python 3.9 and avoid Python 3.10 as *vpype* is not yet compatible). Secondly, ``pip`` will successfully install all dependencies so using system packages is not required.

Using MacPorts
--------------

After `installing MacPorts <https://www.macports.org/install.php>`_, make sure its port database is up-to-date::

  $ sudo port selfupdate
  $ sudo port upgrade outdated

Then, install the required ports::

  $ sudo port install python39

Optionally, you may make Python 3.9 the default interpreter::

  $ sudo port select --set python python39

Create the virtual environment using the full path to the python interpreter::

  $ /opt/local/bin/python3.9 -m venv vpype_venv


Using the official Python distribution
--------------------------------------

After running the Python installer, the virtual environment can readily be created::

  $ /Library/Frameworks/Python.framework/Versions/3.9/bin/python3 -m venv vpype_venv


Activating the virtual environment and installing *vpype*
---------------------------------------------------------

Activate the virtual environment::

  $ source vpype_venv/bin/activate

Install *vpype* (note the prompt now reflecting the activated virtual environment)::

  (vpype_venv) $ pip install "vpype[all]"

You can test that *vpype* is fully functional by checking its version and displaying some random lines::

  (vpype_venv) $ vpype --version
  vpype 1.8.0
  (vpype_venv) $ vpype random show

Since *vpype* is installed within a virtual environment, it must be activated each time a new terminal window is opened::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed without activating the virtual environment by using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help



Windows
=======

.. highlight:: bat

A Windows installer is `available here <https://github.com/abey79/vpype/releases>`__. Although this installation method is easier, it does not allow plug-ins to be installed. If plug-ins are required, a manual installation is recommended.

First, Python must be installed. Python 3.9 is recommended, although it is also compatible with Python 3.7 and later. The official Python distribution for Windows can be `downloaded here <https://www.python.org/downloads/>`__.

First, create a virtual environment for your *vpype* installation, launch the ``cmd`` terminal and enter the following commands::

  > python -m venv vpype_venv

This will create a ``vpype_venv`` directory which will contain everything needed to run *vpype*. Before using an environment, you need to activate it::

  > vpype_venv\Scripts\activate.bat

You will need to activate your virtual environment each time you launch a new  terminal. With your virtual environment activated, type the following command to install *vpype*::

  (vpype_venv) > pip install vpype[all]

Note how the prompt now reflect the fact that the ``vpype_venv`` virtual environment is currently active.

You should now be able to use *vpype*. Type this for a list of command::

  (vpype_venv) > vpype --help

This command should open a window showing a circle::

  (vpype_venv) > vpype circle 0 0 10cm show

If you can see it, your installation is up and running!


Linux
=====

.. highlight:: bash

First, you must ensure that a Python interpreter with compatible version (3.7 to 3.9) is installed on your system. This is best done using your system's package manager. On Debian/ubuntu flavored installation, this is typically done as follows::

  $ sudo apt-get install python3 python3-pip

The preferred way to install *vpype* is in a dedicated `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_. Follow these steps to do so::

  $ python3 -m venv vpype_venv      # create a new virtual environment
  $ source vpype_venv/bin/activate  # activate the newly created virtual environment
  (vpype_venv) $ pip install --upgrade pip
  (vpype_venv) $ pip install 'vpype[all]'

You should now be able to run *vpype*::

  $ vpype --help

Each time a new terminal window is opened, the virtual environment must be activated using::

  $ source vpype_venv/bin/activate

Alternatively, *vpype* can be executed using the full path to the executable::

  $ /path/to/vpype_venv/bin/vpype --help


Raspberry Pi
============

Full installation including the viewer on the Raspberry Pi is no longer supported. Expert users may succeed with ``pip install vpype[all]`` provided that a suitable version of the PySide2 package is available. Also, the new viewer requires OpenGL 3.3, which the Raspberry Pi does not support. The classic viewer should work correctly::

  $ vpype [...] show --classic

Installing the CLI-only version described in the next section is easier and should be favored whenever possible. Here are the recommended steps to do so.

Some packages and their dependencies are easier to install at the system level::

  $ sudo apt-get install python3-shapely python3-numpy python3-scipy

Then, create a virtual environment with access to the globally installed packages::

  $ python3 -m venv --system-site-package vpype_venv

Finally, activate the virtual environment, install, and run *vpype*::

  $ source vpype_venv/bin/activate
  (vpype_venv) $ pip install vpype
  (vpype_venv) $ vpype --help


CLI-only install
================

For special cases where the :ref:`cmd_show` is not needed and dependencies such as matplotlib, PySide2, or ModernGL are difficult to install, a CLI-only version of *vpype* can be installed using this command::

  $ pip install vpype

Note the missing ``[all]`` compared the instructions above.
