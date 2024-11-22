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
root_scope = SyntaxPackageScope(type="package", name="*global", prevscope=None,visibility="public")
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
    print("======符号表======")
    print(root_scope)


# 可能属于program，或者package，注意作用域
def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''
    pass


# todo 差一个open path
def p_decls(p):
    '''Decls : Const_block
    | Type_block
    | Sensor_block
    | Group_block
    | Package_decl
    | User_op_decl
    '''


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
        p[0].fields=dict()
        p[0].fields.update(p[2].value)
        p[0].fields.update(p[3].value)
        return
    if len(p) == 4:
        # 数组定义，最后一个声明，放着不管！todo
        return
    if p[1].value == "signed" or p[1].value == "unsigned":
        # signed/unsigned的两个声明，类型为signed unsigned
        p[0] = SyntaxType(type=p[1].value)
        p[0].integerNum=int(p[3].value)
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


#常数声明，在const_decl中加入到对应scope中
def p_const_block(p):
    'Const_block : CONST Const_block_1'

def p_const_block_1(p):
    '''Const_block_1 : Const_decl SEMICOLON Const_block_1
    | empty'''

def p_const_decl(p):
    '''Const_decl : Interface_status LV6ID COLON Type_expr
    | Interface_status LV6ID COLON Type_expr EQU INTEGERNUM'''

    #todo const_decl这里的interNum应该是expr，在写完expr后补上

    if not "Visibility" in p[1].keys():
        visibility="public"
    else:visibility=p[1]["Visibility"]
    p[0]=SyntaxConstSymbol(name=p[2].value,visibility=visibility)
    p[0].syntaxType=p[4]
    if "External" in p[1].keys():
        p[0].isImported = True
    else:
        p[0].isImported = False
        p[0].integerNum=int(p[6].value)
    global cur_scope
    cur_scope.add_constSymbol(p[0])

#sensor声明，在sensor_decl中加入对应scope中
def p_sensor_block(p):
    'Sensor_block : SENSOR Sensor_block_1'
def p_sensor_block_1(p):
    '''Sensor_block_1 : Sensor_decl SEMICOLON Sensor_block_1
    | empty'''
def p_sensor_decl(p):
    'Sensor_decl : Id_one_or_more_with_comma COLON Type_expr'
    global cur_scope
    for ID in p[1]:
        sensor_symbol=SyntaxSensorSymbol(name=ID)
        sensor_symbol.syntaxType=p[3]
        cur_scope.add_sensorSymbol(sensor_symbol)

#group声明，在group_decl部分加入scope
#group是一个只有一层的type数组
def p_group_block(p):
    '''Group_block : GROUP Group_block_1'''
def p_group_block_1(p):
    '''Group_block_1 : Group_decl SEMICOLON Group_block_1
                     | empty'''
def p_group_decl(p):
    '''Group_decl : Visibility_zero_or_one LV6ID EQU Group_expr'''

    if p[1] and "Visibility" in p[1].keys():
        visibility=p[1]["Visibility"]
    else: visibility="public"
    p[0]=SyntaxGroupSymbol(name=p[2].value,visibility=visibility)
    p[0].groupExpr=p[4]
    global cur_scope
    cur_scope.add_groupSymbol(p[0])
def p_group_expr(p):
    '''Group_expr : LPARENTHESE Type_expr Group_expr_1 RPARENTHESE'''
    p[0] = list()
    p[0].append(p[2])
    p[0] += p[3]
def p_group_expr_1(p):
    '''Group_expr_1 : COMMA Type_expr Group_expr_1
                    | empty'''
    p[0]=list()
    if len(p)!=2:
        p[0].append(p[2])
        p[0]+=p[3]

#package声明，注意修改当前作用域，并添加其到子作用域之中
def p_package_decl(p):
    'Package_decl : PACKAGE Package_decl_1 Decls_zero_or_more END SEMICOLON'
    #遍历完成，恢复作用域
    global cur_scope
    cur_scope=cur_scope.prevScope
def p_package_decl_1(p):
    'Package_decl_1 : Visibility_zero_or_one Pack_Lv6id'
    #在这里修改作用域
    if p[1] and "Visibility" in p[1].keys():
        visibility=p[1]["Visibility"]
    else: visibility="public"
    global cur_scope
    scope = SyntaxPackageScope(type="package",name=p[2].value,prevscope=cur_scope,visibility=visibility)
    cur_scope.add_childScope(scope)
    cur_scope=scope

def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0]=p[1]


#user_op_decl部分，这里是连接上下层scope的通道，注意修改作用域并添加符号表
def p_user_op_decl(p):
    'User_op_decl : User_op_name User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    #遍历结束，换回作用域
    global cur_scope
    cur_scope=cur_scope.prevScope
def p_user_op_name(p):
    '''User_op_name : Op_kind Interface_status User_op_decl_Lv6id'''
    #切换作用域
    global cur_scope
    if "Visibility" in p[2].keys():
        visibility=p[2]["Visibility"]
    else: visibility="public"
    user_op_scope=SyntaxUserOp(type=p[1]["Op_kind"],name=p[3].value,prevscope=cur_scope,visibility=visibility)
    cur_scope.add_userOp(user_op_scope)
    cur_scope=user_op_scope
def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0]=dict()
    p[0]["Op_kind"]=p[1].value
def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
def p_user_op_decl_1(p):
    '''User_op_decl_1 : Size_decl
                      | empty'''
def p_size_decl(p):
    '''Size_decl : LSHIFT Id_one_or_more_with_comma RSHIFT
                 | LSHIFT RSHIFT'''
    global cur_scope
    if len(p)==4:
        cur_scope.set_sizeDecl(p[2])
def p_in_params(p):
    'In_Params : Params'
def p_out_params(p):
    'Out_Params : Params'
def p_params(p):
    'Params : LPARENTHESE Params_1 RPARENTHESE'
def p_params_1(p):
    '''Params_1 : Var_decls Params_2
    | empty'''
def p_params_2(p):
    '''Params_2 : SEMICOLON Var_decls Params_2
    | empty'''
def p_user_op_decl_2(p):
    '''User_op_decl_2 : Where_decl
                        | empty'''
def p_where_decl(p):
    '''Where_decl : WHERE Typevar Where_decl_1 Numeric_kind'''
    p[0]=dict()
    typevars=list()
    typevars.append(p[2].value)
    typevars+=p[3]
    cur_scope.numericKind=p[4]["Numeric_kind"]
    cur_scope.whereDecl=typevars#更新whereDecl
def p_where_decl_1(p):
    '''Where_decl_1 : COMMA Typevar Where_decl_1
                    | empty'''
    p[0]=list()
    if len(p)!=2:
        p[0].append(p[2].value)
        p[0]+=p[3]
def p_user_op_decl_3(p):
    '''User_op_decl_3 : Spec_decl
                        | empty'''
def p_spec_decl(p):
    '''Spec_decl : SPECIALIZE Path_id'''
    cur_scope.speceDecl=p[2].value#更新spec
#这里差不多就是data_def，只不过这里必须要有let tel部分，并且可以就只写一个冒号，基本上就是完全一样
def p_opt_body(p):
    '''Opt_body : SEMICOLON'''
    #todo 后面再具体实现
    # | Equation SEMICOLON
    # | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    # | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL'''

#变量声明 todo 下一步就是他
def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
def p_var_id_1(p):
    '''Var_id_1 : CLOCK
    | empty'''
def p_var_id_2(p):
    '''Var_id_2 : PROBE
    | empty'''
def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
def p_var_decls_2(p):
    '''Var_decls_2 : When_decl
                    | empty'''
def p_when_decl(p):
    '''When_decl : WHEN Clock_expr'''
def p_clock_expr(p):
    '''Clock_expr : LV6ID
    | NOT LV6ID
    | LPARENTHESE LV6ID MATCH Pattern RPARENTHESE'''
def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | Pattern_1 INTEGERNUM
    | Pattern_1 TYPED_INTEGER
    | Bool_atom
    | UNDERLINE'''
def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
def p_var_decls_3(p):
    '''Var_decls_3 : Default_decl
    | empty'''
def p_var_decls_4(p):
    '''Var_decls_4 : Last_decl
    | empty'''

#todo 等expr！default和last的decl部分
def p_default_decl(p):
    '''Default_decl : empty'''
def p_last_decl(p):
    '''Last_decl : empty'''

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

# path_id，返回lex_value，path只搜索package！
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
