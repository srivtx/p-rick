#!/usr/bin/env python3
"""Validate a Colab notebook: every code cell must parse as IPython
(shell-magic lines replaced), every cell source must be a string list."""
import ast
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else \
    'code/p-027-cifar-colab.ipynb'
nb = json.load(open(path))
n_code = n_md = 0
for i, c in enumerate(nb['cells']):
    assert isinstance(c['source'], list), f'cell {i}: source not a list'
    src = ''.join(c['source'])
    if c['cell_type'] == 'code':
        n_code += 1
        import re
        py = '\n'.join(
            (re.sub(r'^(\s*)[!%]\S.*$', r'\1pass', l)
             if re.match(r'^\s*[!%]\S', l) else l)
            for l in src.split('\n'))
        py = py.replace('!{cmd}', 'pass')
        try:
            ast.parse(py)
        except SyntaxError as e:
            print(f'cell {i} SYNTAX ERROR line {e.lineno}: {e.text}')
            ls = py.split('\n')
            for j in range(max(0, e.lineno - 3),
                           min(len(ls), e.lineno + 2)):
                print('   ', j + 1, repr(ls[j]))
            sys.exit(1)
    else:
        n_md += 1
print(f'{path}: OK — {n_code} code cells parse, {n_md} markdown cells')
