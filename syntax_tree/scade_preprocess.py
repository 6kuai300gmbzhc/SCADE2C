from ply.yacc import yacc
import re
import argparse
from scade_lex import *
from SyntaxClass import *
import os

scade_lexer = scade_lex()
precedence = (
    ('left', 'ARROW'),
    ('left', 'LOR', 'LXOR'),
    ('left', 'LAND'),
    ('left', 'OR', 'XOR'),
    ('left', 'AND'),
    ('left', 'EQU', 'NOEQU', 'LESSEQU', 'GREATEREQU', 'LESS', 'GREATER'),
    ('left', 'LSL', 'LSR'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'STAR', 'MOD', 'DIVIDE'),
    # ('right', 'UMINUS', 'UPLUS'),
    ('left', 'PRE'),
    ('right', 'NOT', 'LNOT'),
    ('left', 'EXPONENT'),
    ('left', 'POINT')
)
root_scope = SyntaxPackageScope(Kind="package", Name="*global", PrevScope=None)
cur_scope = root_scope


def p_program(p):
    'Program : Decls_zero_or_more'
    reOrderScope(root_scope)

def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''

def p_decls(p):
    'Decls : empty'
    pass
def p_empty(p):
    'empty :'
    pass

def get_parse(input_path: str, root_operator: str):
    parser = yacc(debug=1, start="Program")

    file = open(input_path, 'r')
    strs = file.read()

    pattern1 = r'#pragma [a-zA-Z0-9_!"$#%&\'()*+,\-./:;_<=>?@\\^`|{}~\s]*?#end'
    strs = re.sub(pattern1, '', strs, flags=re.MULTILINE)

    pattern2 = r'\#[\w]+'
    strs = re.sub(pattern2, '', strs)

    pattern3 = re.compile(r'/\*.*?\*/', re.DOTALL)
    strs = re.sub(pattern3, '', strs)

    print("=======strs=====\n", strs)
    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)
    # writeFile(programNode)


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-r', '--root_operator', required=True, type=str)
    args = argParser.parse_args()
    get_parse(args.input_path, args.root_operator)
