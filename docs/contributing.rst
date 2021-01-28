.. _contributing:

============
Contributing
============

How can you help?
=================

Contributions are most welcome and there  are many ways you can help regardless of your fluency with software development:

* First and foremost, do provide feedback on what you do with *vpype* and how you do it, either on the `DrawingBots Discord server`_ or by filling an `issue`_. This knowledge is critically important to improve *vpype*.
* Write an `issue`_ for any problem or friction point you encounter during the installation or use of *vpype* or for any feature you feel is missing.
* Make the present documentation better by fixing typos and improve the quality of the text (English is *not* the main author's native language).
* Write cookbook recipes for new workflows.
* Improving the test coverage and contributing to CI/CD aspects is welcome — and a good way to become familiar with the code.
* Improve existing features or contribute entirely new ones with a `pull request`_. If you plan on creating new commands, consider making a :ref:`plugin <plugins>` first — it will be easy to integrate it into *vpype*'s codebase later on if it makes sense.


.. _issue: https://github.com/abey79/vpype/issues

.. _pull request: https://github.com/abey79/vpype/pulls

.. _DrawingBots Discord server: https://discordapp.com/invite/XHP3dBg


Development guidelines:

* Write tests for your code (this project uses `pytest <https://docs.pytest.org/>`_).
* Use `black <https://github.com/psf/black>`_ for code formatting and `isort <https://pycqa.github.io/isort/>`_ for
  consistent imports.


Development environment
=======================

.. highlight:: bash

*vpype* uses `Poetry <https://python-poetry.org>`_ for packaging and dependency management and its `installation
<https://python-poetry.org/docs/#installation>`_ is required to prepare the development environment::

  $ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

(See Poetry's documentation for alternative means of installation.)

You can then download *vpype*, prepare a virtual environment and install all dependencies with a few commands::

  $ git clone https://github.com/abey79/vpype.git
  $ cd vpype
  $ poetry install

You can execute *vpype* (which installed in the project's virtual environment managed by Poetry) with the ``poetry
run`` command::

  $ poetry run vpype --help

Alternatively, you can activate the virtual environment and then directly use *vpype*::

  $ poetry shell
  $ vpype --help

Running the tests
=================

You can run tests with the following command::

  $ poetry run pytest
