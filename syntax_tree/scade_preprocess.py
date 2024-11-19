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
    # ('right', 'UMINUS', 'UPLUS'),todo 用到的时候记得去掉
    ('left', 'PRE'),
    ('right', 'NOT', 'LNOT'),
    ('left', 'EXPONENT'),
    ('left', 'POINT')
)
root_scope = SyntaxPackageScope(type="package", name="*global", prevscope=None)
cur_scope = root_scope

'''
新作用域：
program，package
group，type，const，sensor 附着在上面两个之中
属于SyntaxPackageScope

user_op_decl，比较特别的中间层，属于SyntaxUserOpSymbol因为要给别人调用

control_block(包含状态机和clock_block)
data_def附着在上面两个之中
scope在data_def之中（如果data_def只是一句equation就没有)
然后signal_block和local_block在scope之中
因此这一堆都属于SyntaxDataDefScope

package包含user_op_decl包含data_def
data_def可以自己包含自己
data_def包含equation包含control_block包含状态机/clocked_block包含deta_def
'''


def p_program(p):
    'Program : Decls_zero_or_more'
    reOrderScope(root_scope)
    print(get_syntax_tree(root_scope))


# 可能属于program，或者package，注意作用域
def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''
    pass


# todo 后续加新的block
def p_decls(p):
    '''Decls : Type_block'''


# 类型定义,在type_decl阶段就把类型登记到当前的符号表中去。
def p_type_block(p):
    'Type_block : TYPE Type_block_1'


def p_type_block_1(p):
    '''Type_block_1 : Type_decl SEMICOLON Type_block_1
                    | empty'''

#把类型登记到对应scope的符号表中，有imported和现场声明的两种类型
def p_Type_decl(p):
    'Type_decl : Interface_status LV6ID Type_decl_1 Type_decl_2'
    if not "Visibility" in p[1].keys():
        visibility="public"
    else:visibility=p[1]["Visibility"]

    p[0]=SyntaxTypeSymbol(name=p[2].value,visibility=visibility)
    if "External" in p[1].keys():
        p[0].numericKind=p[4]["Numeric_kind"]
        p[0].isImported=True
    else:
        p[0].syntaxType=p[3]
        p[0].isImported = False
    global cur_scope
    cur_scope.add_typeSymbol(p[0])

def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    if len(p)!=2:
        p[0]=p[2]
        return
    p[0]=None

def p_type_decl_2(p):
    '''Type_decl_2 : IS Numeric_kind
                   | empty'''
    if len(p)!=2:
        p[0]=p[2]
        return
    p[0]=None

def p_numeric_kind(p):
    '''Numeric_kind : NUMERIC
    | FLOAT
    | INTEGER
    | SIGNED
    | UNSIGNED'''
    p[0]=dict()
    p[0]["Numeric_kind"]=p[1].value

def p_type_def(p):
    '''Type_def : Type_expr
                | ENUM LBPARENTHESE Id_one_or_more_with_comma RBPARENTHESE'''
    if len(p)==2:
        p[0]=p[1]
        return
    p[0]=SyntaxType(type="enum")
    p[0].enumList=p[3]

# 返回lex_value,strs:Type_expr,type:为对应子类型type，value，若为基本类型则为type
# 若为path_id，typevar则为id名字，signed，unsigned则为后面跟的数字
def p_type_expr(p):
    '''Type_expr : BOOL
    | SIGNED LSHIFT INTEGERNUM RSHIFT
    | INT8
    | INT16
    | INT32
    | INT64
    | UNSIGNED LSHIFT INTEGERNUM RSHIFT
    | UINT8
    | UINT16
    | UINT32
    | UINT64
    | FLOAT32
    | FLOAT64
    | CHAR
    | Path_id
    | Typevar
    | LBPARENTHESE Field_decl Type_expr_1 RBPARENTHESE'''
    # | Type_expr EXPONENT Expr'''
    # todo 类型定义缺一句 等写完expr部分再来收拾


    if p[1].value == "{":
        p[0] = SyntaxType(type="field_decl")
        p[0].Fields=dict()
        p[0].Fields.update(p[2].value)
        p[0].Fields.update(p[3].value)
        return
    if len(p) == 4:
        # 数组定义，最后一个声明，放着不管！todo
        return
    if p[1].value == "signed" or p[1].value == "unsigned":
        # signed/unsigned的两个声明，类型为signed unsigned
        p[0] = SyntaxType(type=p[1].value)
        p[0].IntegerNum=int(p[3].value)
        return
    # 普通的情况
    p[0]=SyntaxType(type=p[1].value)


def p_field_decl(p):
    '''Field_decl : LV6ID COLON Type_expr'''
    p[0] = lex_value("field_decl")
    p[0].type = p[1].value
    p[0].value = dict()
    p[0].value[p[1].value] = p[3]



def p_type_expr_1(p):
    '''Type_expr_1 : COMMA Field_decl Type_expr_1
    | empty'''
    p[0] = lex_value("type_expr_1")
    p[0].type = "type_expr_1"
    p[0].value = dict()
    if len(p) != 2:
        p[0].value.update(p[2].value)
        p[0].value.update(p[3].value)



# ID 返回列表，存储每个ID
def p_id_one_or_more_with_comma(p):
    'Id_one_or_more_with_comma : LV6ID Id_one_or_more_with_comma_1'
    p[0] = list()
    p[0].append(p[1].value)
    p[0] += p[2]


def p_id_one_or_more_with_comma_1(p):
    '''Id_one_or_more_with_comma_1 : COMMA LV6ID Id_one_or_more_with_comma_1
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2].value)
        p[0] += p[3]

# path_id，返回lex_value，
def p_path_id(p):
    '''Path_id : LV6ID Path_1'''
    p[0] = lex_value("path_id", "")
    p[0].value += p[1].value + p[2].value


def p_path_1(p):
    '''Path_1 : DOUBLECOLON LV6ID Path_1
    | empty '''
    p[0] = lex_value("path_1", "")
    if len(p) != 2:
        p[0].value += p[1].value + p[2].value + p[3].value


# 模板id 返回lex_value
def p_typevar(p):
    '''Typevar : SINGLEQUOTE LV6ID'''
    p[0] = lex_value("typevar", p[1].value + p[2].value)


# 可见性 返回字典，有key：External，Visibility为对应值，没有就NONE
def p_interface_status(p):
    '''Interface_status : Visibility_zero_or_one External
    | Visibility_zero_or_one'''
    p[0] = dict()
    for i in range(1, len(p)):
        if p[i]: p[0].update(p[i])


def p_visibility_zero_or_one(p):
    '''Visibility_zero_or_one : Visibility
    | empty'''
    p[0] = p[1]


def p_external(p):
    'External : IMPORTED'
    p[0] = dict()
    p[0]["External"] = p[1].value


def p_visibility(p):
    '''Visibility : PRIVATE
    | PUBLIC'''
    p[0] = dict()
    p[0]["Visibility"] = p[1].value


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
