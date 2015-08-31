
import sys
import os
import shlex
import mock


#mock_modules_list
MOCK_MODULES = [
  'maya',
  'maya.utils',
  'maya.cmds',
  'maya.mel',
  'maya.api',
  'maya.OpenMaya',
  'maya.OpenMayaUI',
  'maya.api.OpenMaya',
]

sys.modules.update((mod_name, mock.MagicMock()) for mod_name in MOCK_MODULES)
sys.path.insert(0, os.path.abspath('..'))


import mampy


extensions = [
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
]


todo_include_todos = True
add_function_parentheses = True
autodoc_member_order = 'bysource'


templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']

# General information about the project.
project = u'mampy'
copyright = u'2015, Marcus Albertsson'
author = u'Marcus Albertsson'

version = mampy.__version__
release = version

language = None


pygments_style = 'sphinx'


html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
htmlhelp_basename = 'mampydoc'


latex_elements = {}
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
