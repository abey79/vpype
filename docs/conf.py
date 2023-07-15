from __future__ import annotations

import os
import sys

import vpype as vp

# let sphinx find vpype packages
sys.path.insert(0, os.path.abspath("../"))


project = "vpype"
# noinspection PyShadowingBuiltins
copyright = "2020-2022, Antoine Beyeler"
author = "Antoine Beyeler"


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_click.ext",
    "myst_parser",
    "sphinx_copybutton",
]

autodoc_typehints = "both"

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
html_theme = "furo"
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

# -- Substitutions

UNIT_STRINGS = ", ".join(f"``{s}``" for s in sorted(vp.UNITS.keys()))
UNIT_EXPR_STRINGS = ", ".join(f"``{s}``" for s in sorted(vp.UNITS.keys()) if s != "in")

rst_prolog = f"""
.. |units| replace:: {UNIT_STRINGS}
.. |units_expr| replace:: {UNIT_EXPR_STRINGS}
"""


# -- Plausible support
ENABLE_PLAUSIBLE = os.environ.get("READTHEDOCS_VERSION_TYPE", "") in ["branch", "tag"]
html_context = {"enable_plausible": ENABLE_PLAUSIBLE}


# noinspection PyUnusedLocal
def autodoc_skip_member(app, what, name, obj, skip, options):
    # noinspection PyBroadException
    try:
        if "_deprecated" in str(obj.__module__):
            return True
    except:  # noqa: E722
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


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
