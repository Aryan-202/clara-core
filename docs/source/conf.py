"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
import sys

# Path injection: Add the project root to sys.path so Sphinx can import modules from clara/
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'clara-core'
copyright = '2026, Aryan Vishwakarma'
author = 'Aryan Vishwakarma'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'myst_parser',
]

# Source file suffixes
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
suppress_warnings = [
    'ref.python',
    'docutils',
    'app.add_directive',
]

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Autodoc settings
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']


def setup(app):
    """Sphinx extension setup to skip re-exported members in package __init__ files."""
    def skip_imported(app, what, name, obj, skip, options):
        current_module = app.env.temp_data.get('autodoc:module')
        if not current_module:
            return skip

        mod = sys.modules.get(current_module)
        if mod and getattr(mod, '__file__', '').endswith('__init__.py'):
            # In package __init__.py, skip members so submodules hold primary documentation
            return True

        obj_module = getattr(obj, '__module__', None)
        if obj_module and obj_module != current_module:
            return True

        return skip

    app.connect('autodoc-skip-member', skip_imported)
