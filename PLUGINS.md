# Creating _vpype_ plug-ins

## Why?

Thanks to the underlying [Click](https://click.palletsprojects.com/) library, writing plug-ins for _vpype_ is very
easy and makes it a compelling option for your next plotter project. Plug-ins directly benefit from _vpype_'s
facilities, such as SVG export, line optimisation and sorting, scaling and pagination, etc. Plug-ins also benefit from
the Click-inherited facilities to create compelling CLI interfaces to parametrize your plug-in.


## How?

The easiest way to start a _vpype_ plug-in project is to use the [Cookiecutter](https://cookiecutter.readthedocs.io/)
template:

```bash
$ cookiecutter gh:abey79/cookiecutter-vpype-plugin
```

After answering a few question, your project structure will be created. To make it operational, the plug-in and its
dependencies (including _vpype_ itself) must be installed, typically in a local virtual environment:

```bash
$ cd my-vpype-plugin/
$ python -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ pip install --editable .
```

Note the use of the `--editable` flag when installing the plug-in. This means that you can freely edit the source of
the plug-in and it is used by the _vpype_ executable installed in your virtual environment. You can check that that
everything works as expected:

```bash
$ vpype --help
Usage: vpype [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

Options:
  -v, --verbose
  -I, --include PATH  Load commands from a command file.
  --help              Show this message and exit.

Commands:

  [...]

  Plugins:
    my-vpype-plugin  Insert documentation here...
```

By default, plug-in have a single command with the `@generator` decorator:

```python
@click.command()
@generator
def vpype_trash():
    """
    Insert documentation here...
    """
    lc = LineCollection()
    return lc

vpype_trash.help_group = "Plugins"
```

Generator commands must return a `LineCollection` instance, which is currently documented directly in the
[source code](https://github.com/abey79/vpype/blob/master/vpype/model.py). Other types of commands are possible:
`@layer_processor` and `@global_processor` -- check the
[source code](https://github.com/abey79/vpype/blob/master/vpype/decorators.py) for details.


## Getting help

This being a rather young project, documentation may be missing and/or rough around the edges. The author is available
for support on [Drawingbots](https://drawingbots.net)'s [Discord server](https://discordapp.com/invite/XHP3dBg).
