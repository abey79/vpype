# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

# -- Project information -----------------------------------------------------
# noinspection PyPackageRequirements
from recommonmark.parser import CommonMarkParser

project = "vpype"
# noinspection PyShadowingBuiltins
copyright = "2020-2022, Antoine Beyeler"
author = "Antoine Beyeler"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_click.ext",
    "sphinx_autodoc_typehints",
    # "recommonmark", # NOTE: see workaround below
    # "alabaster",
    # 'autoapi.extension',
]

# -- Autoapi configuration ------------------------------------------------
# autoapi_dirs = ['../vpype']
# autoapi_options = ['members', 'undoc-members', 'show-inheritance']
# autoapi_generate_api_docs = False

autosummary_generate = True
add_module_names = False
autosummary_imported_members = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "venv", ".*"]

# -- Global options ----------------------------------------------------------

# Don't mess with double-dash used in CLI options
smartquotes_action = "qe"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# html_theme = "alabaster"
# html_theme_path = [alabaster.get_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# -- Intersphinx options
intersphinx_mapping = {
    "shapely": ("https://shapely.readthedocs.io/en/latest/", None),
    "click": ("https://click.palletsprojects.com/en/7.x/", None),
    "python": ("https://docs.python.org/3/", None),
    "Pillow": ("https://pillow.readthedocs.io/en/stable/", None),
}

# -- Napoleon options

napoleon_include_init_with_doc = True


# noinspection PyUnusedLocal
def autodoc_skip_member(app, what, name, obj, skip, options):
    # noinspection PyBroadException
    try:
        if "_deprecated" in str(obj.__module__):
            return True
    except:
        pass

    if name.startswith("__") and name.endswith("__"):
        return True

    exclusions = (
        # vpype/__init__.py
        "_get_version",
        # vpype/config.py
        "CONFIG_MANAGER",
        # vpype_cli/debug.py
        "DebugData",
        # vpype_cli/state.py
        "_current_state",
    )

    return skip or name in exclusions


# RECOMMONMARK WORKAROUND
# see https://github.com/readthedocs/recommonmark/issues/177


class CustomCommonMarkParser(CommonMarkParser):
    def visit_document(self, node):
        pass


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)

    # recommonmark workaround
    app.add_source_suffix(".md", "markdown")
    app.add_source_parser(CustomCommonMarkParser)
