
import sys
import os
import shlex
import mock


MOCK_MODULES = ['maya', 'maya.cmds', 'maya.OpenMaya', 'maya.api.OpenMaya',
                'OpenMaya', 'api.OpenMaya']

sys.modules.update((mod_name, mock.Mock()) for mod_name in MOCK_MODULES)
sys.path.insert(0, os.path.abspath('..'))


extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
]
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'mampy'
copyright = u'2015, Marcus Albertsson'
author = u'Marcus Albertsson'

version = '0.0.1'
release = '0.0.1'

language = None

exclude_patterns = ['_build']

pygments_style = 'sphinx'

todo_include_todos = False

# html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'mampydoc'

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',

# Latex figure (float) alignment
#'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
  (master_doc, 'mampy.tex', u'mampy Documentation',
   u'Marcus Albertsson', 'manual'),
]

man_pages = [
    (master_doc, 'mampy', u'mampy Documentation',
     [author], 1)
]

#  dir menu entry, description, category)
texinfo_documents = [
  (master_doc, 'mampy', u'mampy Documentation',
   author, 'mampy', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
#texinfo_no_detailmenu = False

autodoc_member_order = 'bysource'
