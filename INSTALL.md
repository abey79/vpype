# Installing _vpype_

## Windows

Unfortunately, _vpype_ being a new project, simple installation package are not yet available, so the installation procedure
requires a few steps.

### Installing Python

_vpype_ uses Python. You can find an official installer [here](https://www.python.org/downloads/windows/). Using Python 3.8
is recommanded.

### Installing Git

Git is a widely use version control management. It is needed by the Python package manager. You can find an official
installer [here](https://git-scm.com/download/win).

### Downloading dependancies

Python includes a package manager called `pip` which is able to find and install most dependencies automatically. Some
dependencies must, however, be manually downloaded from the
[Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/) archive:

- [Shapely](https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely)
- [rtree](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rtree)
- [scikit-image](https://www.lfd.uci.edu/~gohlke/pythonlibs/#scikit-image)

For each of these libraries, download the version that corresponds to your Python installation and architecture
(32bit vs. 64bit). In most case, it should be the `*‑cp38‑cp38‑win_amd64.whl` for Python 3.8 and a non-ancient computer.

### Create a virtual environment

"Virtual environments" are environment that you can easily create and delete and in which you install Python-based 
dependencies and software.
It is considered best practice to always use virtual envionments in order to avoid conflicts between projects.

To create a virtual environment for your _vpype_ installation, launch the `cmd` terminal and enter the following commands:

```
python -m venv my-vpype-env
```

This will create a `my-vpype-env` directory which will contain everything needed to run _vpype_.

Before using an environment, you need to activate it:

```
my-vpype-env\Scripts\activate.bat
```

You will need to activate your virtual environment each time you launch a `cmd` terminal.

### Install everything and run _vpype_

With your virtual environment activated, follow these steps to install everything.

If you are using an older version of Python (3.6 or 3.7, upgrade your version of `pip`):

```
pip install --upgrade pip
```

Install the `.whl` files you downloaded earlier:

```
pip install Rtree-0.8.3-cp38-cp38-win_amd64.whl
pip install Shapely-1.6.4.post2-cp38-cp38-win_amd64
pip install scikit_image-0.16.2-cp38-cp38-win_amd64
```

Install `scipy` (another dependency):

```
pip install scipy
```

Install _vpype_:

```
pip install git+https://github.com/abey79/vpype.git#egg=vpype
```

You should now be able to use _vpype_. Type this for a list of command:

```
vpype --help
```

This command should open a window showing a circle:


```
vpype circle 0 0 10cm show
```

If you can see it, your installation is up and running!
