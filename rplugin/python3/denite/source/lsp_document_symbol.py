import logging
import os
from urllib.parse import urlparse

from .base import Base

logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

handler = logging.FileHandler('denitevimlsp.log')
fmt = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler.setFormatter(fmt)
handler.setLevel(logging.CRITICAL)
logger.addHandler(handler)

LSP_SYMBOL_KINDS = [
    'File',
    'Module',
    'Namespace',
    'Package',
    'Class',
    'Method',
    'Property',
    'Field',
    'Constructor',
    'Enum',
    'Interface',
    'Function',
    'Variable',
    'Constant',
    'String',
    'Number',
    'Boolean',
    'Array',
    'Object',
    'Key',
    'Null',
    'EnumMember',
    'Struct',
    'Event',
    'Operator',
    'TypeParameter',
]

OUTLINE_HIGHLIGHT_SYNTAX = [
    {'name': 'File', 'link': 'Type', 're': r'^.\{-}\W'},
    {'name': 'Type', 'link': 'Statement', 're': r'\[.\{-}\]'},
    {'name': 'Pattern', 'link': 'Comment', 're': r'[^\]]+$'}
]

class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'lsp_document_symbol'
        self.kind = 'file'

        self.vim.vars['denite#source#vim_lsp#_results'] = []
        self.vim.vars['denite#source#vim_lsp#_request_completed'] = False

    def gather_candidates(self, context):
        if context['is_async']:
            if self.vim.vars['denite#source#vim_lsp#_request_completed']:
                context['is_async'] = False
                return make_candidates(
                    self.vim.vars['denite#source#vim_lsp#_results'])
            return []

        self.vim.vars['denite#source#vim_lsp#_request_completed'] = False
        context['is_async'] = True
        self.vim.call('denite_vim_lsp#document_symbol')
        return []

    def highlight(self):
        for syn in OUTLINE_HIGHLIGHT_SYNTAX:
            self.vim.command(
                'syntax match {0}_{1} /{2}/ contained containedin={0}'.format(
                    self.syntax_name, syn['name'], syn['re']
                )
            )
            self.vim.command(
                'highlight default link {0}_{1} {2}'.format(
                    self.syntax_name, syn['name'], syn['link']
                )
            )


def make_candidates(symbols):
    if not symbols:
        logger.info('symbol nothing')
        return []
    if not isinstance(symbols, list):
        logger.info('symbol is not list')
        return []
    candidates = [_parse_candidate(symbol) for symbol in symbols]
    return candidates


def _parse_candidate(symbol):
    candidate = {}
    loc = symbol['location']
    url_path = urlparse(loc['uri'])
    relative_path = os.path.relpath(os.path.join(url_path.netloc, url_path.path))
    line = loc['range']['start']['line'] + 1
    col = loc['range']['start']['character'] + 1

    location_display = './{}:{}:{}'.format(relative_path, line, col)

    symbol_type_display = '[{}]'.format(LSP_SYMBOL_KINDS[symbol['kind'] - 1])

    candidate['word'] = '{} {}'.format(symbol['name'], symbol_type_display)

    candidate['abbr'] = '{} {}'.format(candidate['word'], location_display)

    candidate['action__path'] = relative_path
    candidate['action__line'] = line
    candidate['action__col'] = col

    return candidate
