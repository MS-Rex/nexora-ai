# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here.
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------
project = 'Nexora AI'
copyright = '2025, RexFlow Team'
author = 'RexFlow Team'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# Add any Sphinx extension module names here, as strings.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'myst_parser',
    'sphinxcontrib.openapi',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# The theme to use for HTML and HTML Help pages.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Extension configuration -------------------------------------------------
# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Mock imports for modules that can't be imported during doc build
autodoc_mock_imports = [
    'fastapi',
    'pydantic', 
    'sqlalchemy',
    'asyncpg',
    'uvicorn',
    'openai',

    'pydub',
    'numpy',
    'torch',
    'librosa',
    'soundfile',
    'lancedb',
    'tiktoken',
    'pyarrow',
    'pandas',
    'tantivy',
    'pylance'
]

# Type hints settings
typehints_use_signature = True
typehints_use_signature_return = True
typehints_document_rtype = True

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'fastapi': ('https://fastapi.tiangolo.com', None),
    'pydantic': ('https://docs.pydantic.dev/latest', None),
}

# MyST parser settings
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "colon_fence",
]

# HTML theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'style_external_links': True,
    'vcs_pageview_mode': '',
}

# Custom CSS files
html_css_files = [
    'custom.css',
]

# HTML context
html_context = {
    'display_github': True,
    'github_user': 'your-username',  # Update with your GitHub username
    'github_repo': 'nexora-ai',      # Update with your repo name
    'github_version': 'main',
    'conf_py_path': '/docs/',
} 