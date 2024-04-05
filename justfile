# install a complete dev environment
install:
  poetry install -E all --with docs,dev

# update Poetry's lockfile
update-deps:
  poetry update

# run all tests
test:
  pytest

format:
  ruff check --fix --output-format=full vpype vpype_cli vpype_viewer tests

lint:
  mypy
  ruff check --output-format=full vpype vpype_cli vpype_viewer tests
  black --check --diff vpype vpype_cli vpype_viewer tests

# run previously failed tests
test-failed:
  pytest --last-failed

# build the documentation
docs-build:
  sphinx-build -b html docs docs/_build

# run a live server for the documentation
docs-live:
  sphinx-autobuild docs docs/_build/html/

# clean the documentations build file
docs-clean:
  rm -rf docs/_build docs/api
