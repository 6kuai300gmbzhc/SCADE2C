from ply.yacc import yacc
import re
import argparse
from syntax_tree.scade_lex import *
from syntax_tree.SyntaxClass import *
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
    ('right', 'UMINUS', 'UPLUS'),
    ('left', 'PRE'),
    ('right', 'NOT', 'LNOT'),
    ('left', 'EXPONENT'),
    ('left', 'POINT')
)
root_scope = SyntaxPackageScope(type="package", name="*global", prevscope=None, visibility="public")
cur_scope = root_scope

'''
新作用域：
program，package
group，type，const，sensor 附着在上面两个之中
属于SyntaxPackageScope

user_op_decl，比较特别的中间层，属于SyntaxUserOpSymbol因为要给别人调用

control_block(包含状态机和clock_block)
data_def附着在上面两个之中
然后signal_block和local_block在data_def之中
因此这一堆都属于SyntaxDataDefScope


package包含user_op_decl包含data_def
data_def可以自己包含自己
data_def包含equation包含control_block包含状态机/clocked_block包含deta_def
'''


def p_program(p):
    'Program : Decls_zero_or_more'
    print("======符号表======")
    print(root_scope)


# 可能属于program，或者package，注意作用域
def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''
    pass


def p_decls(p):
    '''Decls : Const_block
    | Type_block
    | Sensor_block
    | Group_block
    | Package_decl
    | User_op_decl
    | Open_path
    '''


def p_open_path(p):
    '''Open_path : OPEN Path_id SEMICOLON
    '''
    global cur_scope
    cur_scope.add_open_package(p[2].value)


# 类型定义,在type_decl阶段就把类型登记到当前的符号表中去。
def p_type_block(p):
    'Type_block : TYPE Type_block_1'


def p_type_block_1(p):
    '''Type_block_1 : Type_decl SEMICOLON Type_block_1
                    | empty'''


# 把类型登记到对应scope的符号表中，有imported和现场声明的两种类型
def p_Type_decl(p):
    'Type_decl : Interface_status LV6ID Type_decl_1 Type_decl_2'
    if not "Visibility" in p[1].keys():
        visibility = "public"
    else:
        visibility = p[1]["Visibility"]

    p[0] = SyntaxTypeSymbol(name=p[2].value, visibility=visibility)
    if "External" in p[1].keys():
        p[0].numericKind = p[4]["Numeric_kind"]
        p[0].isImported = True
    else:
        p[0].syntaxType = p[3]
        p[0].isImported = False
    global cur_scope
    cur_scope.add_typeSymbol(p[0])


def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    if len(p) != 2:
        p[0] = p[2]
        return
    p[0] = None


def p_type_decl_2(p):
    '''Type_decl_2 : IS Numeric_kind
                   | empty'''
    if len(p) != 2:
        p[0] = p[2]
        return
    p[0] = None


def p_numeric_kind(p):
    '''Numeric_kind : NUMERIC
    | FLOAT
    | INTEGER
    | SIGNED
    | UNSIGNED'''
    p[0] = dict()
    p[0]["Numeric_kind"] = p[1].value


def p_type_def(p):
    '''Type_def : Type_expr
                | ENUM LBPARENTHESE Id_one_or_more_with_comma RBPARENTHESE'''
    if len(p) == 2:
        p[0] = p[1]
        return
    p[0] = SyntaxType(type="enum")
    p[0].enumList = p[3]


# 返回SyntaxType
def p_type_expr(p):
    '''Type_expr : BOOL
    | SIGNED LSHIFT Expr RSHIFT
    | INT8
    | INT16
    | INT32
    | INT64
    | UNSIGNED LSHIFT Expr RSHIFT
    | UINT8
    | UINT16
    | UINT32
    | UINT64
    | FLOAT32
    | FLOAT64
    | CHAR
    | Path_id
    | Typevar
    | LBPARENTHESE Field_decl Type_expr_1 RBPARENTHESE
    | Type_expr EXPONENT Expr'''
    if p[1].value == "{":
        p[0] = SyntaxType(type="field_decl")
        p[0].fields = dict()
        p[0].fields.update(p[2].value)
        p[0].fields.update(p[3].value)
        return
    if len(p) == 4:
        p[0] = SyntaxType(type="list")
        p[0].listType = p[1]
        p[0].listExpr = p[3]
        return
    if p[1].value == "signed" or p[1].value == "unsigned":
        # signed/unsigned的两个声明，类型为signed unsigned
        p[0] = SyntaxType(type=p[1].value)
        p[0].sizeExpr = p[3]
        return
    # 普通的情况
    p[0] = SyntaxType(type=p[1].strs)
    if p[1].strs == "typevar" or p[1].strs == "path_id":
        p[0].value = p[1].value


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


# 常数声明，在const_decl中加入到对应scope中
def p_const_block(p):
    'Const_block : CONST Const_block_1'


def p_const_block_1(p):
    '''Const_block_1 : Const_decl SEMICOLON Const_block_1
    | empty'''


def p_const_decl(p):
    '''Const_decl : Interface_status LV6ID COLON Type_expr
    | Interface_status LV6ID COLON Type_expr EQU Expr'''

    if not "Visibility" in p[1].keys():
        visibility = "public"
    else:
        visibility = p[1]["Visibility"]
    p[0] = SyntaxConstSymbol(name=p[2].value, visibility=visibility)
    p[0].syntaxType = p[4]
    if "External" in p[1].keys():
        p[0].isImported = True
    else:
        p[0].isImported = False
        p[0].valueExpr = p[6]
    global cur_scope
    cur_scope.add_constSymbol(p[0])


# sensor声明，在sensor_decl中加入对应scope中
def p_sensor_block(p):
    'Sensor_block : SENSOR Sensor_block_1'


def p_sensor_block_1(p):
    '''Sensor_block_1 : Sensor_decl SEMICOLON Sensor_block_1
    | empty'''


def p_sensor_decl(p):
    'Sensor_decl : Id_one_or_more_with_comma COLON Type_expr'
    global cur_scope
    for ID in p[1]:
        sensor_symbol = SyntaxSensorSymbol(name=ID)
        sensor_symbol.syntaxType = p[3]
        cur_scope.add_sensorSymbol(sensor_symbol)


# group声明，在group_decl部分加入scope
# group是一个只有一层的type数组
def p_group_block(p):
    '''Group_block : GROUP Group_block_1'''


def p_group_block_1(p):
    '''Group_block_1 : Group_decl SEMICOLON Group_block_1
                     | empty'''


def p_group_decl(p):
    '''Group_decl : Visibility_zero_or_one LV6ID EQU Group_expr'''

    if p[1] and "Visibility" in p[1].keys():
        visibility = p[1]["Visibility"]
    else:
        visibility = "public"
    p[0] = SyntaxGroupSymbol(name=p[2].value, visibility=visibility)
    p[0].groupExpr = p[4]
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
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


# package声明，注意修改当前作用域，并添加其到子作用域之中
def p_package_decl(p):
    'Package_decl : PACKAGE Package_decl_1 Decls_zero_or_more END SEMICOLON'
    # 遍历完成，恢复作用域
    global cur_scope
    cur_scope = cur_scope.prevScope


def p_package_decl_1(p):
    'Package_decl_1 : Visibility_zero_or_one Pack_Lv6id'
    # 在这里修改作用域
    if p[1] and "Visibility" in p[1].keys():
        visibility = p[1]["Visibility"]
    else:
        visibility = "public"
    global cur_scope
    scope = SyntaxPackageScope(type="package", name=p[2].value, prevscope=cur_scope, visibility=visibility)
    cur_scope.add_childScope(scope)
    cur_scope = scope


def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0] = p[1]


# user_op_decl部分，这里是连接上下层scope的通道，注意修改作用域并添加符号表
def p_user_op_decl(p):
    'User_op_decl : User_op_name User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    # 遍历结束，换回作用域
    global cur_scope
    cur_scope = cur_scope.prevScope


def p_user_op_name(p):
    '''User_op_name : Op_kind Interface_status User_op_decl_Lv6id'''
    # 切换作用域
    global cur_scope
    if "Visibility" in p[2].keys():
        visibility = p[2]["Visibility"]
    else:
        visibility = "public"
    imported = "External" in p[2].keys()
    user_op_scope = SyntaxUserOp(type=p[1]["Op_kind"], name=p[3].value, prevscope=cur_scope,
                                 visibility=visibility,isImported=imported)
    cur_scope.add_userOp(user_op_scope)
    cur_scope = user_op_scope


def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0] = dict()
    p[0]["Op_kind"] = p[1].value


def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0] = p[1]


def p_user_op_decl_1(p):
    '''User_op_decl_1 : Size_decl
                      | empty'''


def p_size_decl(p):
    '''Size_decl : LSHIFT Id_one_or_more_with_comma RSHIFT
                 | LSHIFT RSHIFT'''
    global cur_scope
    if len(p) == 4:
        cur_scope.set_sizeDecl(p[2])


def p_in_params(p):
    'In_Params : Params'
    global cur_scope
    cur_scope.inParams = p[1]
    for para in cur_scope.inParams:
        para.isInput = True


def p_out_params(p):
    'Out_Params : Params'
    global cur_scope
    cur_scope.set_outParams(p[1])


def p_params(p):
    'Params : LPARENTHESE Params_1 RPARENTHESE'
    p[0] = p[2]  # SyntaxVariableSymbol的列表


def p_params_1(p):
    '''Params_1 : Var_decls Params_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0] += p[1]
        p[0] += p[2]


def p_params_2(p):
    '''Params_2 : SEMICOLON Var_decls Params_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0] += p[2]
        p[0] += p[3]


def p_user_op_decl_2(p):
    '''User_op_decl_2 : Where_decl
                        | empty'''


def p_where_decl(p):
    '''Where_decl : WHERE Typevar Where_decl_1 Numeric_kind'''
    p[0] = dict()
    typevars = list()
    typevars.append(p[2].value)
    typevars += p[3]
    cur_scope.numericKind = p[4]["Numeric_kind"]
    cur_scope.whereDecl = typevars  # 更新whereDecl


def p_where_decl_1(p):
    '''Where_decl_1 : COMMA Typevar Where_decl_1
                    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2].value)
        p[0] += p[3]


def p_user_op_decl_3(p):
    '''User_op_decl_3 : Spec_decl
                        | empty'''


def p_spec_decl(p):
    '''Spec_decl : SPECIALIZE Path_id'''
    cur_scope.specDecl = p[2].value  # 更新spec


# 这里差不多就是data_def，只不过这里必须要有let tel部分，并且可以就只写一个冒号，基本上就是完全一样
def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL'''


def p_signal_block_zero_or_one(p):
    '''Signal_block_zero_or_one : Signal_block
    | empty'''


def p_signal_block(p):
    'Signal_block : SIG Id_one_or_more_with_comma SEMICOLON'
    global cur_scope
    cur_scope.set_signalSymbolList(p[2])


def p_local_block_zero_or_one(p):
    '''Local_block_zero_or_one : Local_block
    | empty'''


def p_local_block(p):
    '''Local_block : VAR Local_block_1'''


def p_local_block_1(p):
    '''Local_block_1 : Var_decls SEMICOLON Local_block_1
    | empty'''
    if len(p) == 2: return
    global cur_scope
    cur_scope.add_localSymbols(p[1])


# equation部分，描述各种scade语句，每个语句都要添加到对应scope之中
# 从这里往下只会有SyntaxDataDefScope了
def p_equation_zero_or_more_with_semicolon(p):
    '''Equation_zero_or_more_with_semicolon : Equation SEMICOLON Equation_zero_or_more_with_semicolon
    | empty'''


def p_equation(p):  # 把return 挪到control_block里面了方便声明作用域
    '''Equation : Simple_equation
                | Assert
                | Emission
                | Control_block
                '''
    global cur_scope
    cur_scope.add_equation(p[1])


# 在这里添加到对应scope中
def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    p[0] = SyntaxEquation(type="simple_equation", lhs=p[1], lineno=p.lineno(2))
    p[0].set_expr(p[3])


def p_assert(p):
    '''Assert : ASSUME LV6ID COLON Expr
            | GUARANTEE LV6ID COLON Expr'''
    p[0] = SyntaxEquation(type=p[1].value, lhs=list(), lineno=p.lineno(1))
    p[0].assertID = p[2].value
    p[0].set_expr(p[4])


def p_emission(p):
    '''Emission : EMIT Emission_body'''
    p[0] = p[2]


def p_emission_body(p):
    '''Emission_body : SINGLEQUOTE LV6ID Emission_body_1
                    | LPARENTHESE SINGLEQUOTE LV6ID Emission_body_2 RPARENTHESE Emission_body_1'''
    lhs = list()
    if len(p) == 4:
        lhs.append(p[2].value)
        expr = p[3]
    else:
        lhs.append(p[3].value)
        lhs += p[4]
        expr = p[6]
    p[0] = SyntaxEquation(type="emission", lhs=lhs, lineno=p.lineno(1))
    if expr is not None: p[0].set_expr(expr)


def p_emission_body_1(p):
    '''Emission_body_1 : IF Expr
                        | empty'''
    if len(p) != 2:
        p[0] = p[2]
    else:
        p[0] = None


def p_emission_body_2(p):
    '''Emission_body_2 : COMMA SINGLEQUOTE LV6ID Emission_body_2
                        | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[3].value)
        p[0] += p[4]


# 左值
def p_lhs(p):
    '''Lhs : LPARENTHESE RPARENTHESE
    | Lhs_id Lhs_1'''
    p[0] = list()
    if p[1].value != "(":
        p[0].append(p[1].value)
        p[0] += p[2]


def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2].value)
        p[0] += p[3]


def p_lhs_id(p):
    '''Lhs_id : LV6ID
              | UNDERLINE'''
    p[0] = p[1]


# 自动机和clockblock！会单独开放一个作用域，注意切换当前作用域
# 把return挪到这里面了,这里返回一个填好各项参数的equation，并已经将个子作用域添加到当前作用域中
# return 返回列表。这里要根据情况返回一个equation
# p[1]会返回一个对应的名字
def p_control_block(p):
    '''Control_block : Clocked_block Return
     | State_machine Return'''
    global cur_scope
    cur_scope.hasInternalState_InThisAndPreEnv()
    lhs = cur_scope.get_childScope(p[1]).get_return_symbolTable()
    # 检查ruturn的变量是否符合要求，即显示返回的变量里面有没有lhs以外的东西
    for symbol_name in p[2]:
        if symbol_name == "..":  # 遇到这个说明完成了..只会在最后面
            break
        if symbol_name not in lhs.keys():
            # 没有就报错
            raise UnknownIdentifierException(symbol_name)
    p[0] = SyntaxEquation(type="control_block", lhs=lhs.keys(), lineno=p.lineno(1))
    p[0].controlBlockID = p[1]


def p_id_zero_or_one(p):
    '''Id_zero_or_one : LV6ID
    | empty'''
    if p[1].strs == "Empty":
        p[0] = None
    else:
        p[0] = p[1].value


def p_state_machine(p):  # 返回此状态机的名字
    '''State_machine : State_machine_decl State_machine_1 State_machine_end'''
    p[0] = p[1]
    p.set_lineno(0, p.lineno(1))


def p_state_machine_decl(p):  # 切换作用域
    '''State_machine_decl : AUTOMATON Id_zero_or_one'''
    global cur_scope
    if p[2]:
        name = p[2]
    else:
        name = cur_scope.generate_name_for_subScope()
    p[0] = name
    scope = SyntaxAutomaton(type="automaton", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p.set_lineno(0, p.lineno(1))


def p_state_machine_end(p):  # 切换回来
    '''State_machine_end : empty'''
    global cur_scope
    cur_scope = cur_scope.prevScope


def p_state_machine_1(p):
    '''State_machine_1 : State_decl State_machine_1
                       | empty'''


def p_state_decl(p):  # 一个state就是一个子作用域，注意切换作用域
    '''State_decl : Before_state_data_def State_decl_3 State_data_def State_decl_4'''


def p_before_state_data_def(p):  # 切换作用域
    '''Before_state_data_def : State_decl_1 State_decl_2 STATE State_Lv6id'''
    global cur_scope
    state = SyntaxState(type="automaton_state", name=p[4].value, prevscope=cur_scope, visibility="public")
    state.isInitial = p[1] is not None
    state.isFinal = p[2] is not None
    cur_scope.add_childScope(state)
    cur_scope.add_state(state)
    cur_scope = state


def p_state_data_def(p):  # 重写一个data_def，让当前作用域为SyntaxState
    '''State_data_def :  Equation SEMICOLON
                     | Scope'''


def p_state_decl_1(p):
    '''State_decl_1 : INITIAL
                    | empty'''
    if p[1].strs == "Empty":
        p[0] = None
    else:
        p[0] = p[1].value


def p_state_decl_2(p):
    '''State_decl_2 : FINAL
                    | empty'''
    if p[1].strs == "Empty":
        p[0] = None
    else:
        p[0] = p[1].value


def p_state_decl_3(p):
    '''State_decl_3 : UNLESS State_decl_5
    | empty'''
    if len(p) != 2:
        p[0] = p[2]
        global cur_scope
        cur_scope.set_unlessTransitions(p[2])
    else:
        p[0] = None


def p_state_decl_4(p):  # 在这里恢复作用域到automaton
    '''State_decl_4 : UNTIL State_decl_6 State_decl_7
                    | empty '''
    global cur_scope
    if len(p) != 2:
        if p[2] and len(p[2]) > 0: cur_scope.set_untilTransitions(p[2])
        if p[3]: cur_scope.set_synchroArrow(p[3])
    cur_scope = cur_scope.prevScope


def p_state_decl_5(p):
    '''State_decl_5 : Transition SEMICOLON State_decl_6'''
    p[0] = list()
    p[0].append(p[1])
    p[0] += p[3]


def p_state_decl_6(p):
    '''State_decl_6 : Transition SEMICOLON State_decl_6
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[1])
        p[0] += p[3]


def p_transition(p):
    '''Transition : IF Expr Arrow'''
    p[0] = list()
    p[0].append(p[2])
    p[0].append(p[3])


def p_state_decl_7(p):  # 返回一个arrow对象，没有就返回None
    '''State_decl_7 : SYNCHRO State_decl_8 Fork SEMICOLON
    | empty'''
    if len(p) != 2:
        if p[2]:
            p[3].set_action(p[2])
        p[0] = p[3]
    else:
        p[0] = None


def p_state_decl_8(p):
    '''State_decl_8 : Actions
    | empty'''
    if not isinstance(p[1], lex_value):
        p[0] = p[1]
    else:
        p[0] = None


def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    p[0] = p[1]


# 一个action就是一个data_def，即使只有emit语句也可以是data_def。
# 若为data_def则已经生成好了作用域不用处理
# 若不为则需要自己生成一个作用域
def p_actions(p):
    '''Actions : DO LBPARENTHESE Actions_1 Emission_body Actions_2 RBPARENTHESE
    | DO Data_def'''
    global cur_scope
    if len(p) == 3:
        p[0] = p[2]
    else:
        scope = SyntaxDataDefScope(type="data_def", name=cur_scope.generate_name_for_subScope(), prevscope=cur_scope,
                                   visibility="public")
        cur_scope.add_childScope(scope)
        if not p[3]:
            p[4].emit = False
        scope.add_equation(p[4])
        for equation in p[5]:
            scope.add_equation(equation)
        p[0] = scope.name
        # 不切换作用域，直接新建一个作用域塞到当前作用域里就可以了
    # 更新一下当前作用域的返回值列表，将actions的返回值列表并入state内
    action_scope = cur_scope.get_childScope(p[0])
    cur_scope.returnSymbolsTable.update(action_scope.returnSymbolsTable)


def p_actions_1(p):
    '''Actions_1 : EMIT
    | empty'''
    if p[1].strs == "Empty":
        p[0] = None
    else:
        p[0] = p[1].value


def p_actions_2(p):
    '''Actions_2 : SEMICOLON Actions_1 Emission_body Actions_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        if not p[2]:
            p[3].emit = False
        p[0].append(p[3])
        p[0] += p[4]


def p_arrow(p):  # 给arrow添加actions并返回
    '''Arrow : Actions Fork
    | Fork'''
    if len(p) != 2:
        p[2].set_action(p[1])
        p[0] = p[2]
    else:
        p[0] = p[1]


def p_fork(p):  # 在这里就创建一个arrow对象
    '''Fork : Target
    | IF Expr Arrow Fork_1 Fork_2 END'''
    if len(p) == 2:
        p[0] = SyntaxArrow(type=p[1]["type"], target=p[1]["target"])
    else:
        ifList = list()
        ifList.append([p[2], p[3]])
        ifList += p[4]
        p[0] = SyntaxArrow(type="if", ifExpr=ifList, elseExpr=p[5])


def p_fork_1(p):
    '''Fork_1 : Elsif_fork Fork_1
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[1])
        p[0] += p[2]


def p_fork_2(p):
    '''Fork_2 : Else_fork
    | empty'''
    if isinstance(p[1], lex_value):
        p[0] = None
    else:
        p[0] = p[1]


def p_elsif_fork(p):
    '''Elsif_fork : ELSIF Expr Arrow'''
    p[0] = list()
    p[0].append(p[2])
    p[0].append(p[3])


def p_else_fork(p):
    '''Else_fork : ELSE Arrow'''
    p[0] = p[2]


def p_target(p):
    '''Target : RESTART LV6ID
    | RESUME LV6ID'''
    p[0] = dict()
    p[0]["type"] = p[1].value
    p[0]["target"] = p[2].value


def p_clocked_block(p):
    '''Clocked_block : ACTIVATE Id_zero_or_one Before_match_block Match_block After_clocked_block
     | ACTIVATE Id_zero_or_one Before_if_block If_block After_clocked_block'''
    p[0] = p[3]
    p.set_lineno(0, p.lineno(1))


def p_before_match_block(p):  # 切换作用域
    '''Before_match_block : empty'''
    global cur_scope
    if p[-1]:
        name = p[-1]
    else:
        name = cur_scope.generate_name_for_subScope()
    scope = SyntaxClockedScope(type="match_block", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p[0] = name


def p_after_clocked_block(p):
    '''After_clocked_block : empty'''
    # 这里切换回作用域，并将读取到的block添加到作用域之中
    global cur_scope
    cur_scope.block = p[-1]
    cur_scope = cur_scope.prevScope


def p_match_block(p):
    '''Match_block : WHEN Expr MATCH Match_block_1'''
    p[0] = SyntaxMatchBlock(expr=p[2], matchList=p[4])


def p_match_block_1(p):
    ' Match_block_1 : VERTICALBAR Pattern COLON Data_def Match_block_2 '
    p[0] = list()
    tmp = list()
    tmp.append(p[2])
    tmp.append(p[4])
    p[0].append(tmp)
    p[0] += p[5]


def p_match_block_2(p):
    '''Match_block_2 : VERTICALBAR Pattern COLON Data_def Match_block_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        tmp = list()
        tmp.append(p[2])
        tmp.append(p[4])
        p[0].append(tmp)
        p[0] += p[5]


def p_before_if_block(p):  # 切换作用域
    '''Before_if_block : empty'''
    global cur_scope
    if p[-1]:
        name = p[-1]
    else:
        name = cur_scope.generate_name_for_subScope()
    scope = SyntaxClockedScope(type="if_block", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p[0] = name


def p_if_block(p):
    'If_block : IF Expr THEN If_block_1 ELSE If_block_1'
    p[0] = SyntaxIfBlock(expr=p[2], thenBlock=p[4], elseBlock=p[6])


def p_if_block_1(p):
    '''If_block_1 : Data_def
    | If_block'''
    p[0] = p[1]


# return返回值，返回ID列表,包括..的情况，在equation层进行处理
def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0] = p[2]


def p_returns_var(p):
    '''Returns_var : Returns_var_1 Returns_var_2'''
    p[0] = list()
    p[0] += p[1]
    if p[2] in p[1]:
        # 重复定义，报错
        raise MultipleFlowDefinitionException(p[2])
    else:
        p[0].append(p[2])


def p_returns_var_1(p):
    '''Returns_var_1 : Returns_var_1 LV6ID COMMA
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0] += p[1]
        if p[2].value in p[1]:
            # 重复定义，报错
            raise MultipleFlowDefinitionException(p[2].value)
        else:
            p[0].append(p[2].value)


def p_returns_var_2(p):
    '''Returns_var_2 : LV6ID
    | TPOINT'''
    p[0] = p[1].value


# data_def部分，注意切换作用域，不在scope里切换
# 没有名字，注意给他生成一个名字,返回一个指向此作用域的ID
def p_data_def(p):
    '''Data_def : BeforeDataDef Equation SEMICOLON AfterDataDef
                | BeforeDataDef Scope AfterDataDef'''
    p[0] = p[1]


def p_beforeDataDef(p):
    '''BeforeDataDef : empty'''
    global cur_scope
    name = cur_scope.generate_name_for_subScope()
    scope = SyntaxDataDefScope(type="data_def", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p[0] = name


def p_afterDataDef(p):
    '''AfterDataDef : empty'''
    global cur_scope
    cur_scope = cur_scope.prevScope


def p_scope(p):
    '''Scope : Signal_block_zero_or_one Local_block_zero_or_one Eqs
    | Signal_block_zero_or_one Local_block_zero_or_one'''


def p_eqs(p):
    'Eqs : LET Equation_zero_or_more_with_semicolon TEL'


# expr，表达式的右值，返回Syntaxexpr
def p_expr(p):
    '''Expr : Id_expr
    | Atom
    | Tempo_expr
    | Arith_expr
    | Relation_expr
    | List_expr
    | Switch_expr
    | Bool_expr
    | Struct_expr
    | Array_expr
    | Apply_expr
    | Mixed_constructor'''
    p[0] = p[1]


def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    if len(p) == 2:
        p[0] = SyntaxExpr(type="Id_expr", subtype="Path_id")
        p[0].add_object(p[1].value)
    elif len(p) == 3:
        p[0] = SyntaxExpr(type="Id_expr", subtype="singlequoteLv6id")
        p[0].add_object(p[1].value + p[2].value)
    elif len(p) == 4:
        p[0] = SyntaxExpr(type="Id_expr", subtype="lastSinglequoteLv6id")
        p[0].add_object(p[2].value + p[3].value)
        # 为什么我要在这里把'加上？？现在删不掉了

def p_atom(p):
    '''Atom : Bool_atom
    | INTEGERNUM
    | FLOATNUM
    | CHARACTER
    | TYPED_INTEGER
    | TYPED_FLOAT'''
    if p[1].strs == 'true' or p[1].strs == 'false':
        p[0] = SyntaxExpr(type="Atom", subtype="bool_atom")
    else:
        p[0] = SyntaxExpr(type="Atom", subtype=p[1].strs)
    p[0].add_object(p[1].value)


def p_tempo_expr(p):
    '''Tempo_expr : Expr ARROW Expr
    | PRE Expr
    | FBY LPARENTHESE List SEMICOLON Expr SEMICOLON List RPARENTHESE
    | Expr TIMES Expr
    | Expr WHEN Clock_expr
    | MERGE LPARENTHESE Expr SEMICOLON List Tempo_expr_1 RPARENTHESE'''
    global cur_scope
    cur_scope.hasInternalState_InThisAndPreEnv()
    if len(p) == 3:
        p[0] = SyntaxExpr(type="Tempo_expr", subtype="PRE")
        p[0].add_object(p[2])
    elif len(p) == 4:
        if p[2].strs == "->":
            p[0] = SyntaxExpr(type="Tempo_expr", subtype="ARROW")
        elif p[2].strs == "times":
            p[0] = SyntaxExpr(type="Tempo_expr", subtype="TIMES")
        elif p[2].strs == "when":
            p[0] = SyntaxExpr(type="Tempo_expr", subtype="WHEN")
        p[0].add_object(p[1])
        p[0].add_object(p[3])
    elif p[1].strs == "fby":
        p[0] = SyntaxExpr(type="Tempo_expr", subtype="FBY")
        p[0].add_object(p[3])
        p[0].add_object(p[5])
        p[0].add_object(p[7])
    elif p[1].strs == "merge":
        p[0] = SyntaxExpr(type="Tempo_expr", subtype="MERGE")
        p[0].add_object(p[3])
        p[0].add_object(p[5])
        p[0].add_object(p[6])


def p_tempo_expr_1(p):
    '''Tempo_expr_1 : SEMICOLON List Tempo_expr_1
                    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


def p_arith_expr(p):
    '''Arith_expr : LPARENTHESE Expr COLON Type_expr RPARENTHESE'''
    p[0] = SyntaxExpr(type="Arith_expr", subtype="cast")
    p[0].add_object(p[2])
    p[0].add_object(p[4])


def p_arith_expr_unary(p):
    '''Arith_expr : MINUS Expr %prec UMINUS
    | PLUS Expr %prec UPLUS
    | LNOT Expr'''
    p[0] = SyntaxExpr(type="Arith_expr", subtype="unary")
    p[0].add_object(p[1].value)
    p[0].add_object(p[2])


def p_arith_expr_binOp(p):
    '''Arith_expr : Expr PLUS Expr
    | Expr MINUS Expr
    | Expr STAR Expr
    | Expr DIVIDE Expr
    | Expr MOD Expr
    | Expr LAND Expr
    | Expr LOR Expr
    | Expr LXOR Expr
    | Expr LSL Expr
    | Expr LSR Expr'''
    p[0] = SyntaxExpr(type="Arith_expr", subtype="binOp")
    p[0].add_object(p[1])
    p[0].add_object(p[2].value)
    p[0].add_object(p[3])


def p_relation_expr(p):
    '''Relation_expr : Expr EQU Expr
    | Expr NOEQU Expr
    | Expr LESS Expr
    | Expr GREATER Expr
    | Expr LESSEQU Expr
    | Expr GREATEREQU Expr'''
    p[0] = SyntaxExpr(type="Relation_expr", subtype="Relation_expr")
    p[0].add_object(p[1])
    p[0].add_object(p[2].value)
    p[0].add_object(p[3])


def p_list_expr(p):
    '''List_expr : LPARENTHESE List RPARENTHESE'''
    p[0] = p[2]


def p_list(p):
    '''List : List_1
            | empty'''
    p[0] = SyntaxExpr(type="List_expr", subtype="List_expr")
    if isinstance(p[1], list):
        p[0].add_object(p[1])


def p_list_1(p):
    '''List_1 : Expr List_2'''
    p[0] = list()
    p[0].append(p[1])
    p[0] += p[2]


def p_list_2(p):
    '''List_2 : COMMA Expr List_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr
    | LPARENTHESE CASE Expr OF Switch_expr_1 RPARENTHESE'''
    if p[1].strs == "if":
        p[0] = SyntaxExpr(type="Switch_expr", subtype="IF")
        p[0].add_object(p[2])
        p[0].add_object(p[4])
        p[0].add_object(p[6])
    else:
        p[0] = SyntaxExpr(type="Switch_expr", subtype="CASE")
        p[0].add_object(p[3])
        p[0].add_object(p[5])


def p_switch_expr_1(p):
    'Switch_expr_1 : Case_expr Switch_expr_2'
    p[0] = list()
    p[0].append(p[1])
    p[0] += p[2]


def p_switch_expr_2(p):
    '''Switch_expr_2 : Case_expr Switch_expr_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[1])
        p[0] += p[2]


def p_case_expr(p):
    'Case_expr : VERTICALBAR Pattern COLON Expr'
    p[0] = list()
    p[0].append(p[2])
    p[0].append(p[4])


def p_bool_expr(p):
    '''Bool_expr : NOT Expr
    | HASHTAG LPARENTHESE Hashtag_List RPARENTHESE'''
    if len(p) == 3:
        p[0] = SyntaxExpr(type="Bool_expr", subtype="NOT")
        p[0].add_object(p[2])
    else:
        p[0] = SyntaxExpr(type="Bool_expr", subtype="HASHTAG")
        p[0].add_object(p[3])


def p_hashtag_list(p):
    '''Hashtag_List : Hashtag_List_1
    | empty'''
    p[0] = list()
    if isinstance(p[1], list):
        p[0] += p[1]


def p_hashtag_list_1(p):
    '''Hashtag_List_1 : Expr Hashtag_List_2'''
    p[0] = list()
    p[0].append(p[1])
    p[0] += p[2]


def p_hashtag_list_2(p):
    '''Hashtag_List_2 : COMMA Expr Hashtag_List_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


def p_bool_expr_bin(p):
    '''Bool_expr : Expr AND Expr
    | Expr OR Expr
    | Expr XOR Expr'''
    p[0] = SyntaxExpr(type="Bool_expr", subtype="binOp")
    p[0].add_object(p[1])
    p[0].add_object(p[2].value)
    p[0].add_object(p[3])


def p_struct_expr(p):
    '''Struct_expr : Expr POINT LV6ID
    | LBPARENTHESE Label_expr Struct_expr_1 RBPARENTHESE'''
    if len(p) == 4:
        p[0] = SyntaxExpr(type="Struct_expr", subtype="get")
        p[0].add_object(p[1])
        p[0].add_object(p[3].value)
    else:
        p[0] = SyntaxExpr(type="Struct_expr", subtype="construct")
        labels = list()
        labels.append(p[2])
        labels += p[3]
        p[0].add_object(labels)


def p_struct_expr_1(p):
    '''Struct_expr_1 : COMMA Label_expr Struct_expr_1
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


def p_label_expr(p):
    '''Label_expr : LV6ID COLON Expr'''
    p[0] = list()
    p[0].append(p[1].value)
    p[0].append(p[3])


def p_array_expr(p):
    '''Array_expr : LBRACKET List RBRACKET
    | Expr Index'''
    if len(p) == 4:
        p[0] = SyntaxExpr(type="Array_expr", subtype="list")
        p[0].add_object(p[2])
    else:
        p[0] = SyntaxExpr(type="Array_expr", subtype="get")
        p[0].add_object(p[1])
        p[0].add_object(p[2])


def p_array_expr2(p):
    '''Array_expr : REVERSE Expr
    | Expr AT Expr'''
    if len(p) == 3:
        p[0] = SyntaxExpr(type="Array_expr", subtype="reverse")
        p[0].add_object(p[2])
    else:
        p[0] = SyntaxExpr(type="Array_expr", subtype="at")
        p[0].add_object(p[1])
        p[0].add_object(p[3])


def p_array_expr3(p):
    '''Array_expr : Expr EXPONENT Expr
    | Expr LBRACKET Expr TPOINT Expr RBRACKET'''
    if len(p) == 4:
        p[0] = SyntaxExpr(type="Array_expr", subtype="construct")
        p[0].add_object(p[1])
        p[0].add_object(p[3])
    else:
        p[0] = SyntaxExpr(type="Array_expr", subtype="slice")
        p[0].add_object(p[1])
        p[0].add_object(p[3])
        p[0].add_object(p[5])


def p_array_expr4(p):
    '''Array_expr : LPARENTHESE Expr POINT Array_expr_1 DEFAULT Expr RPARENTHESE
    | TRANSPOSE LPARENTHESE Expr SEMICOLON INTEGERNUM SEMICOLON INTEGERNUM RPARENTHESE'''
    if len(p) == 8:
        p[0] = SyntaxExpr(type="Array_expr", subtype="getdefault")
        p[0].add_object(p[2])
        p[0].add_object(p[4])
        p[0].add_object(p[6])
    else:
        p[0] = SyntaxExpr(type="Array_expr", subtype="transpose")
        p[0].add_object(p[3])
        p[0].add_object(p[5].value)
        p[0].add_object(p[7].value)


def p_array_expr_1(p):
    '''Array_expr_1 : Index Array_expr_2'''
    p[0] = list()
    p[0].append(p[1])
    p[0] += p[2]


def p_array_expr_2(p):
    '''Array_expr_2 : Index Array_expr_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[1])
        p[0] += p[2]


def p_label_or_index(p):
    '''Label_or_index : POINT LV6ID
    | Index'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = SyntaxExpr(type="Id_expr", subtype="ID")
        p[0].add_object(p[2].value)


def p_index(p):
    '''Index : LBRACKET Expr RBRACKET'''
    p[0] = p[2]


def p_apply_expr(p):
    '''Apply_expr : Operator LPARENTHESE List RPARENTHESE'''
    p[0] = SyntaxExpr(type="Apply_expr", subtype="Apply_expr")
    p[0].add_object(p[1])
    p[0].add_object(p[3])


def p_operator(p):
    '''Operator : Prefix
    | LPARENTHESE Prefix LSHIFT Operator_1 RSHIFT RPARENTHESE
    | LPARENTHESE MAKE Path_id RPARENTHESE
    | LPARENTHESE FLATTEN Path_id RPARENTHESE
    | LPARENTHESE Iterator Operator LSHIFT Expr RSHIFT RPARENTHESE
    | LPARENTHESE ACTIVATE Operator EVERY Clock_expr RPARENTHESE
    | LPARENTHESE ACTIVATE Operator EVERY Expr DEFAULT Expr RPARENTHESE
    | LPARENTHESE ACTIVATE Operator EVERY Expr INITIAL DEFAULT Expr RPARENTHESE
    | LPARENTHESE RESTART Operator EVERY Expr RPARENTHESE
    | LPARENTHESE Iterator_mw Operator LSHIFT Expr RSHIFT IF Expr DEFAULT Expr RPARENTHESE
    | LPARENTHESE FOLDW Operator LSHIFT Expr RSHIFT IF Expr RPARENTHESE
    | LPARENTHESE FOLDWI Operator LSHIFT Expr RSHIFT IF Expr RPARENTHESE'''
    length = len(p)
    if length == 2:
        if p[1].strs == "path_id":
            p[0] = SyntaxOperator(subtype="Path_id")
        else:
            p[0] = SyntaxOperator(subtype="PREFIXOP")
        p[0].add_object(p[1].value)
    elif length == 5:
        if p[2].strs == "make":
            p[0] = SyntaxOperator(subtype="make")
        elif p[2].strs == "flatten":
            p[0] = SyntaxOperator(subtype="flatten")
        p[0].add_object(p[3].value)
    elif length == 7:
        if p[2].value == "activate":
            p[0] = SyntaxOperator(subtype="activate")
            p[0].add_object(p[3])
            p[0].add_object(p[5])
        elif p[2].value == "restart":
            p[0] = SyntaxOperator(subtype="restart")
            p[0].add_object(p[3])
            p[0].add_object(p[5])
        else:
            if p[2].strs == "path_id":
                p[0] = SyntaxOperator(subtype="Path_id")
            else:
                p[0] = SyntaxOperator(subtype="PREFIXOP")
            p[0].add_object(p[2].value)
            p[0].add_object(p[4])
    elif length == 8:
        p[0] = SyntaxOperator(subtype="iterator")
        p[0].add_object(p[2].value)
        p[0].add_object(p[3])
        p[0].add_object(p[5])
    elif length == 9:
        p[0] = SyntaxOperator(subtype="activateDefault")
        p[0].add_object(p[3])
        p[0].add_object(p[5])
        p[0].add_object(p[7])
    elif length == 10:
        if p[2].strs == "activate":
            p[0] = SyntaxOperator(subtype="activateInitDefault")
        elif p[2].strs == "foldw":
            p[0] = SyntaxOperator(subtype="foldw")
        elif p[2].strs == "foldwi":
            p[0] = SyntaxOperator(subtype="foldwi")
        p[0].add_object(p[3])
        p[0].add_object(p[5])
        p[0].add_object(p[8])
    elif length == 12:
        p[0] = SyntaxOperator(subtype="iterator_mw")
        p[0].add_object(p[2])
        p[0].add_object(p[3])
        p[0].add_object(p[5])
        p[0].add_object(p[8])
        p[0].add_object(p[10])


def p_prefix(p):
    '''Prefix : Path_id
    | PREFIXOP'''
    p[0] = p[1]
    if p[1].strs == "path_id":
        # 让此句所处的函数级作用域添加此路径作为依赖的函数
        global cur_scope
        cur_scope.add_dependent_function_to_userOp(p[1].value)


def p_operator_1(p):
    '''Operator_1 : Expr Operator_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[1])
        p[0] += p[2]


def p_operator_2(p):
    '''Operator_2 : COMMA Expr Operator_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


def p_iterator(p):
    '''Iterator : MAP
    | FOLD
    | MAPI
    | FOLDI
    | MAPFOLD
    | MAPFOLD INTEGERNUM
    | MAPFOLDI
    | MAPFOLDI INTEGERNUM'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1]
        p[0].value += "_" + p[2].value


def p_iterator_mw(p):
    '''Iterator_mw : MAPW
    | MAPWI
    | MAPFOLDW
    | MAPFOLDW INTEGERNUM
    | MAPFOLDWI
    | MAPFOLDWI INTEGERNUM'''
    if len(p) == 2:
        p[0] = p[1].value
    else:
        p[0] = p[1].value + "_" + p[2].value


def p_mixed_constructor(p):
    '''Mixed_constructor : LPARENTHESE Expr WITH Mixed_constructor_1 EQU Expr RPARENTHESE'''
    p[0] = SyntaxExpr(type="Mixed_constructor", subtype="Mixed_constructor")
    p[0].add_object(p[2])
    p[0].add_object(p[4])
    p[0].add_object(p[6])


def p_mixed_constructor_1(p):
    '''Mixed_constructor_1 : Label_or_index Mixed_constructor_2'''
    p[0] = list()
    p[0].append(p[1])
    p[0] += p[2]


def p_mixed_constructor_2(p):
    '''Mixed_constructor_2 : Label_or_index Mixed_constructor_2
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[1])
        p[0] += p[2]


# 变量声明
# 返回一个SyntaxVariableSymbol的列表，不更新到符号表之中
def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
    var_id_list = list()
    var_id_list.append(p[1])
    var_id_list += p[2]
    for var_id in var_id_list:
        var_id.syntaxType = p[4]
        if p[5]:
            var_id.whenExpr = p[5]
        if p[6]:  # default
            var_id.defaultExpr = p[6]
        if p[7]:  # last
            var_id.lastExpr = p[7]
    p[0] = var_id_list


def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
    p[0] = list()
    if len(p) != 2:
        p[0].append(p[2])
        p[0] += p[3]


def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
    p[0] = SyntaxVariableSymbol(name=p[3].value, isClock=p[1].strs == "clock", isProbe=p[2].strs == "probe")


def p_var_id_1(p):
    '''Var_id_1 : CLOCK
    | empty'''
    p[0] = p[1]


def p_var_id_2(p):
    '''Var_id_2 : PROBE
    | empty'''
    p[0] = p[1]


def p_var_decls_2(p):
    '''Var_decls_2 : When_decl
                    | empty'''
    if isinstance(p[1], SyntaxClockExpr):
        p[0] = p[1]
    else:
        p[0] = None


def p_when_decl(p):
    '''When_decl : WHEN Clock_expr'''
    p[0] = p[2]


# 返回SyntaxClockExpr
def p_clock_expr(p):
    '''Clock_expr : LV6ID
    | NOT LV6ID
    | LPARENTHESE LV6ID MATCH Pattern RPARENTHESE'''
    if len(p) == 2:
        ID = p[1].value
        type = "ID"
    elif len(p) == 3:
        ID = p[2].value
        type = "notID"
    else:
        ID = p[2].value
        type = "pattern"
    p[0] = SyntaxClockExpr(ID=ID, type=type)
    if len(p) == 6:
        p[0].pattern = p[4]


# 返回SyntaxPattern
def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | Pattern_1 INTEGERNUM
    | Pattern_1 TYPED_INTEGER
    | Bool_atom
    | UNDERLINE'''
    p[0] = dict()
    if len(p) == 3:
        type = p[2].strs
        value = p[1].value + p[2].value
    else:
        value = p[1].value
        type = p[1].value
    p[0] = SyntaxPattern(type=type, value=value)


def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
    p[0] = p[1]


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    p[0] = p[1]


def p_var_decls_3(p):
    '''Var_decls_3 : Default_decl
    | empty'''
    if not isinstance(p[1], lex_value):
        p[0] = p[1]
    else:
        p[0] = None


def p_var_decls_4(p):
    '''Var_decls_4 : Last_decl
    | empty'''
    if not isinstance(p[1], lex_value):
        p[0] = p[1]
    else:
        p[0] = None


def p_default_decl(p):
    '''Default_decl : DEFAULT EQU Expr'''
    p[0] = p[3]


def p_last_decl(p):
    '''Last_decl : LAST EQU Expr'''
    p[0] = p[3]


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
    if not isinstance(p[1], lex_value):
        p[0] = p[1]
    else:
        p[0] = None


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
    p[0] = lex_value('Empty', "")


def p_error(p):
    print("error", p)


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
