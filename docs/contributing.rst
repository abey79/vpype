.. _contributing:

============
Contributing
============

How can you help?
=================

This project is young and actively developed. There are many ways in which you can contribute regardless of your fluency with software development:

* First and foremost, do provide feedback on what you do with *vpype* and how you do it, either on the `DrawingBots Discord server`_ or by filling an `issue`_. This knowledge is critically important to improve *vpype*.
* Write an `issue`_ for any problem or friction point you encounter during the installation or use of *vpype* or for any feature you feel is missing.
* Suggest improvements to this documentation (fix typos, improve text clarity, add recipes to the cookbook, etc.) with an `issue`_ or, better yet, implement them in a `pull request`_.
* Improving the test coverage and contributing to CI/CD aspects is welcome — and a good way to become familiar with the code.
* Improve existing features or contribute entirely new ones with a `pull request`_. If you plan on creating new commands, consider making a :ref:`plugin <plugins>` first — it will be easy to integrate it into *vpype*'s codebase later on if it makes sense.


.. _issue: https://github.com/abey79/vpype/issue

.. _pull request: https://github.com/abey79/vpype/pulls

.. _DrawingBots Discord server: https://discordapp.com/invite/XHP3dBg


Development guidelines:

* Write tests for your code (this project uses `pytest <https://docs.pytest.org/>`_).
* Use `black <https://github.com/psf/black>`_ for code formatting.


Development environment
=======================

The first step is to download the code:

.. code-block:: bash

  $ git clone https://github.com/abey79/vpype.git

Then, create a virtual environment, update pip and install development dependencies:

.. code-block:: bash

  $ cd vpype
  $ python3 -m venv venv
  $ source venv/bin/activate
  $ pip install --upgrade pip
  $ pip install -r requirements.txt

Finally, install your copy of *vpype* in editable mode:

.. code-block:: bash

  $ pip install --editable .

The ``vpype`` executable will then be available in the terminal and be based on the actual source. If you are using an
IDE, point its run/debug configuration to ``venv/bin/vpype``.


Running the tests
=================

You can run tests with the following command:

.. code-block:: bash

  $ pytest
