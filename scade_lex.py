import ply.lex as lex
import sys

class lex_value:
    def __init__(self, strs = "", value = "", Type = "") -> None:
        self.strs = strs
        self.value = value
        self.type = Type
        self.objects = list()
        # self.values1 = list()
 
    def __repr__(self) -> str:
        strs = str(self.strs) + ' ' + str(self.value)
        return strs

reserved = {
    'include':"INCLUDE",
    'package':"PACKAGE",
    'body':"BODY",
    'end':"END",
    'uses':"USES",
    'is':"IS",
    'provides':"PROVIDES",
    'unsafe':"UNSAFE",
    'node':"NODE",
    'function':"FUNCTION",
    'returns':"RETURNS",
    'type':"TYPE",
    'model':"MODEL",
    'needs':"NEEDS",
    'const':"CONST",
    'var':"VAR",
    'when':"WHEN",
    'enum':"ENUM",
    'struct':"STRUCT",
    'bool':"BOOL",
    'int':"INT",
    'real':"REAL",
    'extern':"EXTERN",
    'not':"NOT",
    'and':"AND",
    'or':"OR",
    'xor':"XOR",
    'div':"DIV",
    'mod':"MOD",
    'if':"IF",
    'then':"THEN",
    'else':"ELSE",
    'let':"LET",
    'tel':"TEL",
    'assert':"ASSERT",
    'step':"STEP",
    'pre':"PRE",
    'current':"CURRENT",
    'fby':"FBY",
    'with':"WITH",
    'nor':"NOR",
    'merge':"MERGE",
    'true':"TRUE",
    'false':"FALSE",
    'last' : "LAST",
    'default' : "DEFAULT",
    'group' : "GROUP",
    'reverse' : "REVERSE",
    'transpose' : "TRANSPOSE",
    'initial' : "INITIAL",
    'float' : "FLOAT",
    'float32' : "FLOAT32",
    'float64' : "FLOAT64",
    'int' : "INT",
    'int8' : "INT8",
    'int16' : "INT16",
    'int32' : "INT32",
    'int64' : "INT64",
    # scade new token
    'activate': "ACTIVATE",
    'assume': "ASSUME",
    'case': "CASE",
    'char': "CHAR",
    'clock': "CLOCK",
    'every': "EVERY",
    'flatten': "FLATTEN",
    'fold': "FOLD",
    'foldi': "FOLDI",
    'foldw': "FOLDW",
    'foldwi': "FOLDWI",
    'guarantee': "GUARANTEE",
    'imported': "IMPORTED",
    'integer': "INTEGER",
    'land': "LAND",
    'lnot': "LNOT",
    'lor': "LOR",
    'lsl': "LSL",
    'lsr': "LSR",
    'lxor': "LXOR",
    'make': "MAKE",
    'map': "MAP",
    'mapfold': "MAPFOLD",
    'mapfoldi': "MAPFOLDI",
    'mapfoldw': "MAPFOLDW",
    'mapfoldwi': "MAPFOLDWI",
    'mapi': "MAPI",
    'mapw': "MAPW",
    'mapwi': "MAPWI",
    'match': "MATCH",
    'numeric': "NUMERIC",
    'of': "OF",
    'open': "OPEN",
    'private': "PRIVATE",
    'probe': "PROBE",
    'public': "PUBLIC",
    'sensor': "SENSOR",
    'signed': "SIGNED",
    'specialize': "SPECIALIZE",
    'times': "TIMES",
    'uint8': "UINT8",
    'uint16': "UINT16",
    'uint32': "UINT32",
    'uint64': "UINT64",
    'unsigned': "UNSIGNED",
    'where': "WHERE",
    # scade automaton reserved
    'automaton': "AUTOMATON",
    'final': "FINAL",
    'state': "STATE",
    'unless': "UNLESS",
    'until': "UNTIL",
    'restart': "RESTART",
    'resume': "RESUME",
    'sig': "SIG",
    'emit': "EMIT",
    'synchro': "SYNCHRO",
    'do': "DO",
    'elsif': "ELSIF"
}

tokens = [
    "INTCONST",  # ++
    "REALCONST",  # ++
    "LV6ID",  # id
    "LV6IDREF",  # ++
    'LBRACKET',  # [
    'RBRACKET',  # ]
    'LPARENTHESE',  # (
    'RPARENTHESE',  # )
    'LBPARENTHESE',  # {
    'RBPARENTHESE',  # }
    'LSHIFT',  # <<
    'RSHIFT',  # >>
    'COMMA',  # ,
    'SEMICOLON',  # ;
    'COLON',  # :
    'EQU',  # =
    'LESS',  # <
    'GREATER',  # >
    'NOEQU',  # <>
    'LESSEQU',  # <=
    'GREATEREQU',  # >=
    'PLUS',  # +
    'MINUS',  # -
    'STAR',  # *
    'DIVIDE',  # /
    'SURPLUS',  # %
    'ARROW',  # ->
    'HASHTAG',  # #
    'EXPONENT',  # ^
    'SHIFT',  # =>
    'POINT',  # .
    'TPOINT',  # ..
    'VERTICALBAR',  # |
    'SINGLEQUOTE',  # '
    'AT',  # @
    'INTEGERNUM'  # ++
] + list(reserved.values())

t_BOOL = r'bool'
t_REAL = r'real'
t_IF = r'if'
t_STRUCT = r'struct'
t_FALSE = r'false'
t_FBY = r'fby'
t_NODE = r'node'
t_AND = r'and'
t_OR = r'or'
t_XOR = r'xor'
t_PACKAGE = r'package'
t_LET = r'let'
t_INT = r'int'
t_PROVIDES = r'provides'
t_END = r'end'
t_FUNCTION = r'function'
t_INCLUDE = r'include'
t_IS = r'is'
t_PRE = r'pre'
t_TYPE = r'type'
t_NEEDS = r'NEEDS'
t_EXTERN = r'extern'
t_CURRENT = r'current'
t_DIV = r'div'
t_ASSERT = r'assert'
t_RETURNS = r'returns'
t_USES = r'uses'
t_MOD = r'mod'
t_ENUM = r'enum'
t_TEL = r'tel'
t_BODY = r'body'
t_NOR = r'nor'
t_MERGE = r'merge'
t_CONST = r'const'
t_UNSAFE = r'unsafe'
t_TRUE = r'true'
t_WITH = r'with'
t_NOT = r'not'
t_THEN = r'then'
t_ELSE = r'else'
t_STEP = r'step'
t_VAR = r'var'
t_WHEN = r'when'
t_LAST = r'last'
t_DEFAULT = r'default'
t_GROUP = r'group'
t_REVERSE = r'reverse'
t_TRANSPOSE = r'transpose'
t_INITIAL = r'initial'
t_FLOAT = r'float'
t_FLOAT32 = r'float32'
t_FLOAT64 = r'float64'
t_INT8 = r'int8'
t_INT16 = r'int16'
t_INT32 = r'int32'
t_INT64 = r'int64'
t_LESSEQU = r'<='
t_LSHIFT = r'<<'
t_NOEQU = r'<>'
t_GREATEREQU = r'>='
t_ARROW = r'->'
t_RSHIFT = r'>>'
t_SHIFT = r'=>'
t_TPOINT = r'\.\.'
t_LBRACKET = r'\['
t_COMMA = r','
t_RBRACKET = r'\]'
t_LPARENTHESE = r'\('
t_RPARENTHESE = r'\)'
t_STAR = r'\*'
t_MINUS = r'-'
t_PLUS = r'\+'
t_LBPARENTHESE = r'{'
t_RBPARENTHESE = r'}'
t_HASHTAG = r'\#'
t_EQU = r'='
t_COLON = r':'
t_DIVIDE = r'/'
t_SURPLUS = r'%'
t_LESS = r'<'
t_EXPONENT = r'\^'
t_POINT = r'\.'
t_SEMICOLON = r';'
t_GREATER = r'>'
t_VERTICALBAR = r'\|'
t_SINGLEQUOTE = r'\''
t_AT = r'\@'
t_ignore = ' \t'
# scade reserved
t_ACTIVATE = r'activate'  
t_ASSUME   = r'assume'  
t_CASE   = r'case'  
t_CHAR   = r'char'  
t_CLOCK   = r'clock'  
t_EVERY   = r'every'
t_FLATTEN   = r'flatten'  
t_FOLD   = r'fold'  
t_FOLDI   = r'foldi'  
t_FOLDW   = r'foldw'  
t_FOLDWI   = r'foldwi'  
t_GUARANTEE   = r'guarantee'  
t_IMPORTED   = r'imported'  
t_INTEGER   = r'integer'  
t_LAND  = r'land'  
t_LNOT  = r'lnot'  
t_LOR   = r'lor'  
t_LSL   = r'lsl'  
t_LSR   = r'lsr'  
t_LXOR  = r'lxor'  
t_MAKE  = r'make'  
t_MAP   = r'map'  
t_MAPFOLD   = r'mapfold'  
t_MAPFOLDI   = r'mapfoldi'  
t_MAPFOLDW   = r'mapfoldw'  
t_MAPFOLDWI   = r'mapfoldwi'  
t_MAPI   = r'mapi'  
t_MAPW   = r'mapw'  
t_MAPWI  = r'mapwi'  
t_MATCH   = r'match'
t_NUMERIC = r'numeric'  
t_OF  = r'of'  
t_OPEN   = r'open'  
t_PRIVATE   = r'private'  
t_PROBE   = r'probe'  
t_PUBLIC   = r'public'  
t_SENSOR   = r'sensor'  
t_SIGNED   = r'signed'  
t_SPECIALIZE   = r'specialize'  
t_TIMES   = r'times'  
t_UINT8   = r'uint8'  
t_UINT16   = r'uint16'  
t_UINT32   = r'uint32'  
t_UINT64   = r'uint64'  
t_UNSIGNED   = r'unsigned'  
t_WHERE  = r'where'

# scade automaton
t_AUTOMATON = r'automaton'
t_FINAL = r'final'
t_STATE = r'state'
t_UNLESS = r'unless'
t_UNTIL = r'until'
t_RESTART = r'restart'
t_RESUME = r'resume'
t_SIG = r'sig'
t_EMIT = r'emit'
t_SYNCHRO = r'synchro'
t_DO = r'do'
t_ELSIF = r'elsif'


def t_REALCONST(t):
    r'\d+\.\d+'
    t.value = lex_value('realconst', float(t.value))
    return t

def t_INTCONST(t):
    r'\d+'
    t.value = lex_value('intconst', int(t.value))
    return t

def t_INTEGERNUM(t):
    r'^(0b[01]+|0[0-7]+|\d+|0x[0-9a-fA-F]+)$'
    t.value=lex_value('integernum',t.value)
    return t

def t_LV6ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'LV6ID')
    if not reserved.get(t.value):
        t.value = lex_value('lv6id', t.value)
    else:
        t.value = lex_value(t.value, t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print("Illegal charactor '%s'" % t.value[0])
    t.lexer.skip(1)

def get_tokens(inputString):
    lexer.input(inputString)
    string_tokens = list()
    while True:
        tok = lexer.token()
        if not tok:
            break
        if type(tok.value) == str:
            tok.value = lex_value(tok.value, tok.value)
        string_tokens.append(tok)
    return string_tokens

class scade_lex:
    def __init__(self):
        self.toks = list()
        self.index = 0

    def set_tokens(self, toks):
        self.index = 0
        self.toks = toks

    def token(self):
        if self.index >= len(self.toks):
            return None
        tmp = self.toks[self.index]
        self.index += 1
        return tmp

    def input(self, strs):
        pass

    def output_program(self, f):
        cur_line = self.toks[0].lineno
        f.write("--------------program----------------\n")
        for tok in self.toks:
            if cur_line != tok.lineno:
                cur_line = tok.lineno
            f.write(str(tok.value.value) + " ")
        f.write("--------------------------------------\n")

lexer = lex.lex()

if __name__ == '__main__':
    data = '''
package NoPackage const d:int32=0;end;
    '''
    toks = get_tokens(data)
    for tok in toks:
        print(tok, tok.value.strs)
    lex_ = scade_lex()
    lex_.set_tokens(toks)
    lex_.output_program(sys.stdout)
