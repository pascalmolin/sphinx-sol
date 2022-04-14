#!/usr/bin/python
#coding: utf8

from docutils.parsers.rst import Directive, directives
from docutils import nodes
#from sphinx.application import ExtensionError
from sphinx import addnodes
import os, shutil
from tempfile import mkdtemp

from sphinx.util import logging
logger = logging.getLogger(__name__)
logger.info('loading extension %s'%__name__)

__version__ = '0.1'

sol_show_symbol = 'solution%s &#8690;'
sol_hide_symbol = '&#8689; solution%s'

sol_highlight = {
  'sage': 'python',
  'xcas': 'mupad',
  'gp': 'gp',
  'python': 'python',
}

"""
declare new solution node
"""
class solution(nodes.Element):
  pass

"""
processing solution environments
during rendering phase
"""

"""
latex wrapper:
solution environment to be defined
in tp stylesheet
"""
def visit_solution_latex(self,node):
  self.body.append('\\begin{solution}\n')
def depart_solution_latex(self,node):
  self.body.append('\\end{solution}\n')

def visit_solution_text(self,node):
  self.body.append('solution :\n')
def depart_solution_text(self,node):
  pass

"""
html render:
wrap solution in show-hide facilities.
"""
def visit_solution_html(self, node):
  #self.body.append(self.starttag(node, 'div', '', CLASS=('solution')))
  ID = node.targetid
  subsol = node.get('select','')
  if subsol:
    subsol = " %s" % subsol
  else:
    subsol = ""
  show_symbol = self.document.settings.env.config.solution_show_symbol % subsol
  hide_symbol = self.document.settings.env.config.solution_hide_symbol % subsol
  self.body.append("""
      <div id='%s' class='folded%s'>
      <span class='toggle-show' onclick='javascript:ToggleId("%s")'>%s</span>
      <span class='toggle-hide' onclick='javascript:ToggleId("%s")'>%s</span>
      <div class='solution'>""" % (ID,subsol,ID,show_symbol,ID,hide_symbol) )
  #self.set_first_last(node)
  #raise ExtensionError('OK')

def depart_solution_html(self, node):
  self.body.append("</div></div>")

class SolutionDirective(Directive):
  has_content = True
  required_arguments = 0
  optional_arguments = 1
  #final_argument_whitespace = True
  option_spec = {
      'language': directives.unchanged,
      'show':directives.unchanged
      }

  def run(self):
    # get document settings
    env = self.state.document.settings.env
    html_context = env.config.html_context

    node = solution()
    node.document = self.state.document
    node.line = self.lineno
    node.targetid = "solution-%d" % env.new_serialno('solution')
    self.state.nested_parse(self.content,self.content_offset, node,
        match_titles=1)


    # classes
    if self.arguments:
        language = self.arguments[0]
    else:
        language = self.options.get('language','').strip()

    if 'latex' in env.app.builder.name:
        return []
    else:
        return [node]

    """
    remove if language not configured
    """
    if language:
        if language not in env.config['tp_solutions_languages']:
            return []

        node['select'] = language

        """
        add language to html_contexts
        this is the way I found to retrieve
        the information at the template level
        """
        if 'tp_solutions_languages' not in html_context:
          html_context['tp_solutions_languages'] = {'show' : [language]}
        elif language not in html_context['tp_solutions_languages']['show']:
          html_context['tp_solutions_languages']['show'].append(language)

        if language in sol_highlight:
            node += [addnodes.highlightlang(lang=sol_highlight[language],
                                        linenothreshold=10)]

    if env.app.config.tp_include_solutions:
        return [node]
    else:
        return []

class LanguagesDirective(Directive):
  has_content = False
  required_arguments = 1
  final_argument_whitespace = True

  def run(self):
    config = self.state.document.settings.env.config
    html_context = config.html_context
    langs = self.arguments[0].split(' ')
    config['tp_solutions_languages'] = langs
    html_context['tp_solutions_languages'] = {'show': langs}
    return []

class RemoveSolutions(Directive):
  def run(self):
    self.state.document.settings.env.app.config.tp_include_solutions = False
    return []

class SolutionStyle(Directive):
  required_arguments = 1
  def run(self):
    arg = self.arguments[0].strip()
    if arg == 'no':
        self.state.document.settings.env.app.config.tp_include_solutions = False
    elif arg == 'yes':
        self.state.document.settings.env.app.config.tp_include_solutions = True
    else:
        logger.warning('unknown argument %s in directive %s'%(arg,__name__))
    return []

#def purge_solutions(app, env, docname):
#  if not hasattr(env, 'solution_all_solutions'):
#    return
#  env.solution_all_solutions = [solution for solution in env.solution_all_solutions
#      if solution['docname'] != docname]


def process_solution_nodes(app, doctree, fromdocname):
  # remove solutions if I don't want them
  # either globally or because lang
  if app.builder.__class__.__name__ == 'LaTeXBuilder':
  #or not app.config.tp_include_solutions:
    for node in doctree.traverse(solution):
      node.parent.remove(node)
  else:
    for node in doctree.traverse(solution):
      if 'select' in node:
        if node['select'] not in app.config.tp_solutions_languages:
          node.parent.remove(node)

### copied from sphinxcontrib.katex
### allows to put stylesheet and gp.js here

def setup_static_path(app):
    app._solution_static_path = mkdtemp()
    if app._solution_static_path not in app.config.html_static_path:
        app.config.html_static_path.append(app._solution_static_path)

def copy_contrib_file(app, file_name):
    pwd = os.path.abspath(os.path.dirname(__file__))
    source = os.path.join(pwd, file_name)
    dest = os.path.join(app._solution_static_path, file_name)
    if os.path.exists(source+'_t'):
        source += '_t'
        dest += '_t'
    copyfile(source, dest)

def builder_inited(app):

    filename_css = 'solution.css'
    filename_js = 'solution.js'

    # Sphinx 1.8 renamed `add_stylesheet` to `add_css_file` and
    # `add_javascript` to `add_js_file`.
    add_css = getattr(app, 'add_css_file', getattr(app, 'add_stylesheet'))
    add_js = getattr(app, 'add_js_file', getattr(app, 'add_javascript'))

    # Ensure the static path is setup to hold KaTeX CSS and autorender files
    setup_static_path(app)

    # custom js and CSS
    copy_contrib_file(app, filename_css)
    add_css(filename_css)

    copy_contrib_file(app, filename_js)
    add_js(filename_js)

def builder_finished(app, exception):
    # Delete temporary dir used for _static file
    shutil.rmtree(app._solution_static_path)

def config_inited(app, config):
    global solution_include, solution_languages
    solution_include = config.tp_include_solution
    solution_languages = config.tp_solution_languages

def setup(app):

  # add the node class
  app.add_node(solution,
               html=(visit_solution_html, depart_solution_html),
               latex=(visit_solution_latex, depart_solution_latex),
               text=(visit_solution_text, depart_solution_text))

  app.add_config_value('solution_show_symbol',sol_show_symbol,'html')
  app.add_config_value('solution_hide_symbol',sol_hide_symbol,'html')

  app.add_config_value('solution_selector','','html')
  app.add_config_value('tp_include_solutions', True, 'env')
  app.add_config_value('tp_solutions_languages', [], 'env')

  #app.connect('doctree-resolved', process_solution_nodes)
  #app.connect('env-purge-doc', purge_solutions)

  app.add_directive('solution', SolutionDirective)
  app.add_directive('solutionstyle', SolutionStyle)

  return {'version': __version__, 'parallel_read_safe': True}

  """ FIXME:
      by default conf.py resets latex_elements
      need to put this in conf.py

      must use the copy_file techniques used in katex (and gp)
  """
  #app.config.latex_elements['preamble'] = '\\usepackage{tp}'
  #app.config.latex_elements['extrapackages'] = r'\usepackage{tp}'
  #app.config.latex_additional_files = ['mesmaths.sty','tp.sty']

  # add stylesheets after env inited
  app.connect('builder-inited', builder_inited)
  app.connect('build-finished', builder_finished)

  #app.config.latex_documents['documentclass'] = 'mesTP'
  #app.add_config_value('html_context', {}, 'html')
  #app.add_directive('solutionlangs', LanguagesDirective)
