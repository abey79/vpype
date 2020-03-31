# Contributing

This project is at an early stage and welcomes all types of contributions. The most important way to contribute is by
[filling Issues](https://github.com/abey79/vpype/issues) describing bugs you are experiencing or features you would
like to see added. Understanding your use-case and workflow is key for _vpype_ to evolve in the right direction.
 
Of course, this is not to say that code contributions are not welcome. Feel free to also open [Pull
requests](https://github.com/abey79/vpype/pulls) to contribute actual code. Note that this project uses
[`black`](https://github.com/psf/black) for code formatting so we don't have to discuss about it.


## Development environment

The first step is to download the code:

```bash
$ git clone https://github.com/abey79/vpype.git
```

Then, create a virtual environment, update pip and install development dependencies:

```bash
$ cd vpype
$ python3 -m venv venv
$ souce venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
```

Finally, install your copy of _vpype_ as editable package:

```
$ pip install -e .
```

The `vpype` executable will then be available in the terminal and be based on the actual source. If you are using an
IDE, point its run/debug configuration to `venv/bin/bin/vpype`. 


## Running the tests

You can run tests with the following command:

```bash
$ pytest
```