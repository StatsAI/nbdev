# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/09_processors.ipynb.

# %% auto 0
__all__ = ['strip_ansi', 'hide_', 'hide_line', 'filter_stream_', 'clean_magics', 'lang_identify', 'rm_header_dash', 'rm_export',
           'exec_show_docs', 'clean_show_doc', 'insert_warning', 'add_frontmatter', 'add_show_docs']

# %% ../nbs/09_processors.ipynb 3
import ast

from .read import *
from .imports import *
from .process import *

from fastcore.imports import *
from fastcore.xtras import *

# %% ../nbs/09_processors.ipynb 10
_re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(cell):
    "Strip Ansi Characters."
    for outp in cell.get('outputs', []):
        if outp.get('name')=='stdout': outp['text'] = [_re_ansi_escape.sub('', o) for o in outp.text]

# %% ../nbs/09_processors.ipynb 13
def hide_(nbp, cell):
    "Hide cell from output"
    del(cell['source'])

# %% ../nbs/09_processors.ipynb 15
_re_hideline = re.compile(r'#\|\s*hide_line\s*$', re.MULTILINE)
def hide_line(cell):
    "Hide lines of code in code cells with the directive `hide_line` at the end of a line of code"
    if cell.cell_type == 'code' and _re_hideline.search(cell.source):
        cell.source = '\n'.join([c for c in cell.source.splitlines() if not _re_hideline.search(c)])

# %% ../nbs/09_processors.ipynb 17
def filter_stream_(nbp, cell, *words):
    "Remove output lines containing any of `words` in `cell` stream output"
    if not words: return
    for outp in cell.get('outputs', []):
        if outp.output_type == 'stream':
            outp['text'] = [l for l in outp.text if not re.search('|'.join(words), l)]

# %% ../nbs/09_processors.ipynb 19
_magics_pattern = re.compile(r'^\s*(%%|%).*', re.MULTILINE)

def clean_magics(cell):
    "A preprocessor to remove cell magic commands"
    if cell.cell_type == 'code': cell.source = _magics_pattern.sub('', cell.source).strip()

# %% ../nbs/09_processors.ipynb 21
_langs = 'bash|html|javascript|js|latex|markdown|perl|ruby|sh|svg'
_lang_pattern = re.compile(rf'^\s*%%\s*({_langs})\s*$', flags=re.MULTILINE)

def lang_identify(cell):
    "A preprocessor to identify bash/js/etc cells and mark them appropriately"
    if cell.cell_type == 'code':
        lang = _lang_pattern.findall(cell.source)
        if lang:
            lang = lang[0]
            if lang=='js': lang='javascript'  # abbrev provided by jupyter
            cell.metadata.language = lang

# %% ../nbs/09_processors.ipynb 24
_re_hdr_dash = re.compile(r'^#+\s+.*\s+-\s*$', re.MULTILINE)

def rm_header_dash(cell):
    "Remove headings that end with a dash -"
    src = cell.source.strip()
    if cell.cell_type == 'markdown' and src.startswith('#') and src.endswith(' -'): del(cell['source'])

# %% ../nbs/09_processors.ipynb 26
_exp_dirs = {'export','exporti'}
_hide_dirs = {*_exp_dirs, 'hide','default_exp'}

def rm_export(cell):
    "Remove cells that are exported or hidden"
    if cell.directives_.keys() & _hide_dirs: del(cell['source'])

# %% ../nbs/09_processors.ipynb 28
_re_exps = re.compile(r'^\s*#\|\s*(?:export|exporti)').search

def _show_docs(trees):
    return [t for t in trees if isinstance(t,ast.Expr) and nested_attr(t, 'value.func.id')=='show_doc']

# %% ../nbs/09_processors.ipynb 29
_imps = {ast.Import, ast.ImportFrom}

def _do_eval(cell):
    trees = cell.parsed_()
    if cell.cell_type != 'code' or not trees: return False
    if cell.directives_.keys() & _exp_dirs or filter_ex(trees, risinstance(_imps)): return True
    if _show_docs(trees): return True
    return False

# %% ../nbs/09_processors.ipynb 30
class exec_show_docs:
    "Execute cells needed for `show_docs` output, including exported cells and imports"
    def __init__(self):
        self.k = NBRunner()
        self.k('from nbprocess.showdoc import show_doc')

    def __call__(self, cell):
        if not _do_eval(cell): return
        self.k.run(cell)

# %% ../nbs/09_processors.ipynb 32
_re_showdoc = re.compile(r'^show_doc', re.MULTILINE)
def _is_showdoc(cell): return cell['cell_type'] == 'code' and _re_showdoc.search(cell.source)

def clean_show_doc(cell):
    "Remove ShowDoc input cells"
    if not _is_showdoc(cell): return
    cell.source = '#| echo: false\n' + cell.source

# %% ../nbs/09_processors.ipynb 34
def insert_warning(nb):
    "Insert Autogenerated Warning Into Notebook after the first cell."
    content = "<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->"
    nb.cells.insert(1, mk_cell(content, False))

# %% ../nbs/09_processors.ipynb 38
_re_title = re.compile(r'^#\s+(.*)[\n\r](?:^>\s+(.*))?', flags=re.MULTILINE)
_re_fm = re.compile(r'^---.*\S+.*---', flags=re.DOTALL)

def _celltyp(nb, cell_type): return nb.cells.filter(lambda c: c.cell_type == cell_type)
def _frontmatter(nb): return _celltyp(nb, 'raw').filter(lambda c: _re_fm.search(c.get('source', '')))

def _title(nb): 
    "Get the title and description from a notebook from the H1"
    md_cells = _celltyp(nb, 'markdown').filter(lambda c: _re_title.search(c.get('source', '')))
    if not md_cells: return None,None
    cell = md_cells[0]
    title,desc=_re_title.match(cell.source).groups()
    cell['source'] = None
    return title,desc

def add_frontmatter(nb):
    "Insert front matter if it doesn't exist"
    if _frontmatter(nb): return
    title,desc = _title(nb)
    if title:
        desc = f'description: "{desc}"\n' if desc else ''
        content = f'---\ntitle: {title}\n{desc}---\n'
        nb.cells.insert(0, NbCell(0, dict(cell_type='raw', metadata={}, source=content)))

# %% ../nbs/09_processors.ipynb 40
_def_types = (ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)
def _def_names(cell, shown):
    return [o.name for o in concat(cell.parsed_()) if isinstance(o,_def_types) and o.name not in shown and o.name[0]!='_']

# %% ../nbs/09_processors.ipynb 41
def add_show_docs(nb):
    "Add show_doc cells after exported cells, unless they are already documented"
    exports = L(cell for cell in nb.cells if _re_exps(cell.source))
    trees = nb.cells.map(NbCell.parsed_).concat()
    shown_docs = {t.value.args[0].id for t in _show_docs(trees)}
    for cell in reversed(exports):
        for nm in _def_names(cell, shown_docs):
            code = f'show_doc({nm})'
            nb.cells.insert(cell.idx_+1, mk_cell(code))
