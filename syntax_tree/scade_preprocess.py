from typing import Optional
from ply.yacc import yacc
import re
import argparse
from syntax_tree.scade_lex import *
import os
import chardet
from syntax_tree.syntax_class.Exceptions import MultipleFlowDefinitionException,UnknownIdentifierException
from syntax_tree.syntax_class.equation import SyntaxEquation, LeftItemId
from syntax_tree.syntax_class.expression import expression_factory
from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.pattern import SyntaxPattern
from syntax_tree.syntax_class.scope.automaton import SyntaxAutomaton, SyntaxState, SyntaxArrow
from syntax_tree.syntax_class.scope.clocked_block import SyntaxClockedScope, SyntaxMatchBlock, SyntaxIfBlock
from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
from syntax_tree.syntax_class.scope.package import SyntaxPackageScope
from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
from syntax_tree.syntax_class.syntaxSymbol import SyntaxConstSymbol, SyntaxSensorSymbol, SyntaxGroupSymbol, \
    SyntaxVariableSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxTypeSymbol, SyntaxType

scade_lexer = scade_lex()
precedence = (
    ('right', 'TIMES'),
    ('left', 'IF','ELSE'),
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
    ('right', 'PRE'),
    ('left', 'REVERSE'),
    ('left', 'WHEN'),
    ('right', 'NOT', 'LNOT'),
    ('left', 'EXPONENT'),
    ('left', 'AT'),
    ('left', 'POINT','LBRACKET')
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
    print("统计")
    for k,v in d.items():
        print(f"{k},{v}")
    print("operator:")
    for k,v in op_d.items():
        print(f"{k},{v}")
    print("iterator:")
    for k,v in it_d.items():
        print(f"{k},{v}")
    print("======符号表======")
    print(root_scope)


# 可能属于program，或者package，注意作用域
def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | Decls'''
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
    '''Open_path : OPEN Path_id SEMICOLON'''
    global cur_scope
    cur_scope.add_open_package(p[2].value)


def p_type_block(p):
    '''Type_block : TYPE
                  | TYPE Type_block_1'''


def p_type_block_1(p):
    '''Type_block_1 : Type_decl SEMICOLON
                    | Type_block_1 Type_decl SEMICOLON'''


def p_Type_decl(p):
    '''Type_decl : Type_decl_head
                 | Type_decl_head EQU Type_def
                 | Type_decl_head IS Numeric_kind
                 | Type_decl_head EQU Type_def IS Numeric_kind'''
    status = p[1]
    if "Visibility" not in status:
        visibility = "public"
    else:
        visibility = status["Visibility"]

    syntax_type = None
    numeric_kind = None
    if len(p) == 4:
        if p[2].value == "=":
            syntax_type = p[3]
        else:
            numeric_kind = p[3]
    elif len(p) == 6:
        syntax_type = p[3]
        numeric_kind = p[5]

    if "External" in status:
        p[0] = SyntaxTypeSymbol(name=status["Name"], syntaxType=syntax_type, visibility=visibility)
        if numeric_kind is not None:
            p[0].numericKind = numeric_kind["Numeric_kind"]
        p[0].isImported = True
    else:
        p[0] = SyntaxTypeSymbol(name=status["Name"], syntaxType=syntax_type, visibility=visibility)
        p[0].isImported = False
    global cur_scope
    cur_scope.add_typeSymbol(p[0])


def p_type_decl_head(p):
    '''Type_decl_head : LV6ID
                      | Visibility LV6ID
                      | IMPORTED LV6ID
                      | Visibility IMPORTED LV6ID'''
    p[0] = {"Name": p[len(p) - 1].value}
    for item in p[1:-1]:
        if isinstance(item, dict):
            p[0].update(item)
        elif item.strs in ("public", "private"):
            p[0]["Visibility"] = item.value
        elif item.strs == "imported":
            p[0]["External"] = item.value

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
    p[0] = SyntaxType(tar_type="enum",scope=cur_scope)
    enum_list = list()
    for enum_value in p[3]:
        enum_symbol=SyntaxConstSymbol(name=enum_value,scope=cur_scope)
        enum_symbol.syntaxType=p[0]
        cur_scope.add_constSymbol(enum_symbol)
        enum_list.append(enum_symbol)
    p[0].enumList=enum_list



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
    | LBPARENTHESE Field_decl RBPARENTHESE
    | LBPARENTHESE Field_decl Type_expr_1 RBPARENTHESE
    | Type_expr EXPONENT Expr'''
    if p[1].value == "{":
        p[0] = SyntaxType(tar_type="field_decl",scope=cur_scope)
        p[0].fields = list()
        p[0].fields.append(p[2].value)
        if len(p) == 5:
            p[0].fields.extend(p[3].value)
        return
    if len(p) == 4:
        p[0] = SyntaxType(tar_type="array",scope=cur_scope)
        p[0].arrayType = p[1]
        p[0].sizeExpr = p[3]
        return
    if p[1].value == "signed" or p[1].value == "unsigned":
        # signed/unsigned的两个声明，类型为signed unsigned
        p[0] = SyntaxType(tar_type=p[1].value)
        p[0].sizeExpr = p[3]
        return
    # 普通的情况
    p[0] = SyntaxType(tar_type=p[1].strs,scope=cur_scope)
    if p[1].strs == "typevar" or p[1].strs == "path_id":
        p[0].value = p[1].value

def p_field_decl(p):
    '''Field_decl : LV6ID COLON Type_expr'''
    p[0] = lex_value("field_decl")
    p[0].type = p[1].value
    type_symbol=SyntaxTypeSymbol(p[1].value,p[3])
    p[0].value = type_symbol


def p_type_expr_1(p):
    '''Type_expr_1 : COMMA Field_decl Type_expr_1
    | COMMA Field_decl'''
    p[0] = lex_value("type_expr_1")
    p[0].type = "type_expr_1"
    p[0].value = list()
    p[0].value.append(p[2].value)
    if len(p) == 4:
        p[0].value.extend(p[3].value)


# 常数声明，在const_decl中加入到对应scope中
def p_const_block(p):
    '''Const_block : CONST
                   | CONST Const_block_1'''


def p_const_block_1(p):
    '''Const_block_1 : Const_decl SEMICOLON
                     | Const_block_1 Const_decl SEMICOLON'''


def p_const_decl(p):
    '''Const_decl : Const_decl_head COLON Type_expr
                  | Const_decl_head COLON Type_expr EQU Expr'''
    global cur_scope
    status = p[1]
    if "Visibility" not in status:
        visibility = "public"
    else:
        visibility = status["Visibility"]
    p[0] = SyntaxConstSymbol(name=status["Name"],scope=cur_scope, visibility=visibility)
    p[0].syntaxType = p[3]
    if "External" in status:
        p[0].isImported = True
    else:
        p[0].isImported = False
        if len(p) == 6:
            p[0].valueExpr = p[5]
    cur_scope.add_constSymbol(p[0])


def p_const_decl_head(p):
    '''Const_decl_head : LV6ID
                       | Visibility LV6ID
                       | IMPORTED LV6ID
                       | Visibility IMPORTED LV6ID'''
    p[0] = {"Name": p[len(p) - 1].value}
    for item in p[1:-1]:
        if isinstance(item, dict):
            p[0].update(item)
        elif item.strs in ("public", "private"):
            p[0]["Visibility"] = item.value
        elif item.strs == "imported":
            p[0]["External"] = item.value


# sensor声明，在sensor_decl中加入对应scope中
def p_sensor_block(p):
    '''Sensor_block : SENSOR
                    | SENSOR Sensor_block_1'''


def p_sensor_block_1(p):
    '''Sensor_block_1 : Sensor_decl SEMICOLON
                      | Sensor_block_1 Sensor_decl SEMICOLON'''


def p_sensor_decl(p):
    'Sensor_decl : Id_one_or_more_with_comma COLON Type_expr'
    global cur_scope
    for ID in p[1]:
        sensor_symbol = SyntaxSensorSymbol(name=ID,scope=cur_scope,syntax_type=p[3])
        cur_scope.add_sensorSymbol(sensor_symbol)


# group声明，在group_decl部分加入scope
# group是一个只有一层的type数组
def p_group_block(p):
    '''Group_block : GROUP
                   | GROUP Group_block_1'''


def p_group_block_1(p):
    '''Group_block_1 : Group_decl SEMICOLON
                     | Group_block_1 Group_decl SEMICOLON'''


def p_group_decl(p):
    '''Group_decl : LV6ID EQU Group_expr
                  | Visibility LV6ID EQU Group_expr'''

    if len(p) == 5:
        visibility = p[1]["Visibility"]
        name = p[2].value
        group_expr = p[4]
    else:
        visibility = "public"
        name = p[1].value
        group_expr = p[3]
    p[0] = SyntaxGroupSymbol(name=name, visibility=visibility)
    p[0].groupExpr = group_expr
    global cur_scope
    cur_scope.add_groupSymbol(p[0])


def p_group_expr(p):
    '''Group_expr : LPARENTHESE Type_expr RPARENTHESE
                  | LPARENTHESE Type_expr Group_expr_1 RPARENTHESE'''
    p[0] = list()
    p[0].append(p[2])
    if len(p) == 5:
        p[0] += p[3]


def p_group_expr_1(p):
    '''Group_expr_1 : COMMA Type_expr
                    | Group_expr_1 COMMA Type_expr'''
    p[0] = list()
    if len(p) == 3:
        p[0].append(p[2])
    else:
        p[0] += p[1]
        p[0].append(p[3])


# package声明，注意修改当前作用域，并添加其到子作用域之中
def p_package_decl(p):
    '''Package_decl : PACKAGE Package_decl_1 END SEMICOLON
                    | PACKAGE Package_decl_1 Decls_zero_or_more END SEMICOLON'''
    # 遍历完成，恢复作用域
    global cur_scope
    cur_scope = cur_scope.prevScope


def p_package_decl_1(p):
    '''Package_decl_1 : Pack_Lv6id
                      | Visibility Pack_Lv6id'''
    # 在这里修改作用域
    if len(p) == 3:
        visibility = p[1]["Visibility"]
        name = p[2].value
    else:
        visibility = "public"
        name = p[1].value
    global cur_scope
    scope = SyntaxPackageScope(type="package", name=name, prevscope=cur_scope, visibility=visibility)
    cur_scope.add_childScope(scope)
    cur_scope = scope


def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0] = p[1]


# user_op_decl部分，这里是连接上下层scope的通道，注意修改作用域并添加符号表
def p_user_op_decl(p):
    '''User_op_decl : User_op_name In_Params RETURNS Out_Params Opt_body
                    | User_op_name Size_decl In_Params RETURNS Out_Params Opt_body
                    | User_op_name In_Params RETURNS Out_Params Where_decl Opt_body
                    | User_op_name In_Params RETURNS Out_Params Spec_decl Opt_body
                    | User_op_name Size_decl In_Params RETURNS Out_Params Where_decl Opt_body
                    | User_op_name Size_decl In_Params RETURNS Out_Params Spec_decl Opt_body
                    | User_op_name In_Params RETURNS Out_Params Where_decl Spec_decl Opt_body
                    | User_op_name Size_decl In_Params RETURNS Out_Params Where_decl Spec_decl Opt_body'''
    # 遍历结束，换回作用域
    global cur_scope
    cur_scope = cur_scope.prevScope

def p_user_op_name(p):
    '''User_op_name : Op_kind User_op_decl_Lv6id
                    | Op_kind Visibility User_op_decl_Lv6id
                    | Op_kind IMPORTED User_op_decl_Lv6id
                    | Op_kind Visibility IMPORTED User_op_decl_Lv6id'''
    # 切换作用域
    global cur_scope
    visibility = "public"
    imported = False
    for item in p[2:-1]:
        if isinstance(item, dict):
            if "Visibility" in item:
                visibility = item["Visibility"]
            if "External" in item:
                imported = True
        elif item.strs in ("public", "private"):
            visibility = item.value
        elif item.strs == "imported":
            imported = True
    user_op_scope = SyntaxUserOp(type=p[1]["Op_kind"], name=p[len(p) - 1].value, prevscope=cur_scope,
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
    '''Params : LPARENTHESE RPARENTHESE
              | LPARENTHESE Var_decls RPARENTHESE
              | LPARENTHESE Var_decls Params_tail RPARENTHESE'''
    if len(p) == 3:
        p[0] = []
    elif len(p) == 4:
        p[0] = list(p[2])
    else:
        p[0] = list(p[2])
        p[0] += p[3]


def p_params_tail(p):
    '''Params_tail : SEMICOLON Var_decls
                   | Params_tail SEMICOLON Var_decls'''
    if len(p) == 3:
        p[0] = list(p[2])
    else:
        p[0] = list(p[1])
        p[0] += p[3]


def p_where_decl(p):
    '''Where_decl : WHERE Typevar Numeric_kind
                  | WHERE Typevar Where_decl_1 Numeric_kind'''
    p[0] = dict()
    typevars = list()
    typevars.append(p[2].value)
    if len(p) == 5:
        typevars += p[3]
        numeric_kind = p[4]
    else:
        numeric_kind = p[3]
    cur_scope.numericKind = numeric_kind["Numeric_kind"]
    for typevar in typevars:
        cur_scope.add_type_var(typevar)
    # 更新whereDecl


def p_where_decl_1(p):
    '''Where_decl_1 : COMMA Typevar Where_decl_1
                    | COMMA Typevar'''
    p[0] = list()
    p[0].append(p[2].value)
    if len(p) == 4:
        p[0] += p[3]


def p_spec_decl(p):
    '''Spec_decl : SPECIALIZE Path_id'''
    cur_scope.specDecl = p[2].value  # 更新spec


# 这里差不多就是data_def，只不过这里必须要有let tel部分，并且可以就只写一个冒号，基本上就是完全一样
def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON
    | LET Equation TEL
    | LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | LET Equation_zero_or_more_with_semicolon TEL
    | Signal_block_local_block LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | Signal_block_local_block LET Equation_zero_or_more_with_semicolon TEL'''


def p_signal_block(p):
    'Signal_block : SIG Id_one_or_more_with_comma SEMICOLON'
    global cur_scope

    cur_scope.set_signalSymbolList(p[2])


def p_signal_block_local_block(p):
    '''Signal_block_local_block : Signal_block
                                | Local_block
                                | Signal_block Local_block'''


def p_local_block(p):
    '''Local_block : VAR
                   | VAR Local_block_1'''


def p_local_block_1(p):
    '''Local_block_1 : Var_decls SEMICOLON
                     | Local_block_1 Var_decls SEMICOLON'''
    global cur_scope
    symbols = p[1] if len(p) == 3 else p[2]
    for symbol in symbols:
        cur_scope.add_localSymbol(symbol)


# equation部分，描述各种scade语句，每个语句都要添加到对应scope之中
# 从这里往下只会有SyntaxDataDefScope了
def p_equation_zero_or_more_with_semicolon(p):
    '''Equation_zero_or_more_with_semicolon : Equation SEMICOLON
                                            | Equation_zero_or_more_with_semicolon Equation SEMICOLON'''


def p_equation(p):  # 把return 挪到control_block里面了方便声明作用域
    '''Equation : Simple_equation
                | Assert
                | Emission
                | Clocked_equation
                | Control_block
                '''
    global cur_scope
    cur_scope.add_equation(p[1])


# 在这里添加到对应scope中
def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    p[0] = SyntaxEquation(type="simple_equation", lhs=p[1], lineno=p.lineno(2),scope=cur_scope)
    p[0].set_expr(p[3])


def p_assert(p):
    '''Assert : ASSUME LV6ID COLON Expr
            | GUARANTEE LV6ID COLON Expr'''
    p[0] = SyntaxEquation(type=p[1].value, lhs=[LeftItemId(cur_scope,"_")], lineno=p.lineno(1),scope=cur_scope)
    p[0].assertID = p[2].value
    p[0].set_expr(p[4])


def p_emission(p):
    '''Emission : EMIT Emission_body'''
    p[0] = p[2]


def p_emission_body(p):
    '''Emission_body : SINGLEQUOTE LV6ID
                    | SINGLEQUOTE LV6ID IF Expr
                    | LPARENTHESE SINGLEQUOTE LV6ID RPARENTHESE
                    | LPARENTHESE SINGLEQUOTE LV6ID Emission_body_2 RPARENTHESE
                    | LPARENTHESE SINGLEQUOTE LV6ID Emission_body_2 RPARENTHESE IF Expr'''
    lhs = list()
    if len(p) == 3:
        lhs.append(LeftItemId(cur_scope,p[2].value))
        expr = expression_factory(type="Atom",sub_type="bool_atom",scope=cur_scope,objects=["true"])
    elif len(p) == 5:
        if p[1].value == "(":
            lhs.append(LeftItemId(cur_scope,p[3].value))
            expr = expression_factory(type="Atom",sub_type="bool_atom",scope=cur_scope,objects=["true"])
        else:
            lhs.append(LeftItemId(cur_scope,p[2].value))
            expr = p[4]
    elif len(p) == 6:
        lhs.append(LeftItemId(cur_scope,p[3].value))
        lhs += p[4]
        expr = expression_factory(type="Atom",sub_type="bool_atom",scope=cur_scope,objects=["true"])
    else:
        lhs.append(LeftItemId(cur_scope,p[3].value))
        lhs += p[4]
        expr = p[6]
    p[0] = SyntaxEquation(type="emission", lhs=lhs, lineno=p.lineno(1),scope=cur_scope)
    p[0].set_expr(expr)


def p_emission_body_2(p):
    '''Emission_body_2 : COMMA SINGLEQUOTE LV6ID
                        | Emission_body_2 COMMA SINGLEQUOTE LV6ID'''
    p[0] = list()
    if len(p) == 4:
        p[0].append(LeftItemId(cur_scope,p[3].value))
    else:
        p[0] += p[1]
        p[0].append(LeftItemId(cur_scope,p[4].value))


# 左值
def p_lhs(p):
    '''Lhs : Lhs_id
           | Lhs_id Lhs_1'''
    p[0] = list()
    p[0].append(p[1])
    if len(p) == 3:
        p[0] += p[2]
def p_lhs_empty(p):
    '''Lhs : LPARENTHESE RPARENTHESE'''
    p[0]=list()
def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | COMMA Lhs_id'''
    p[0] = list()
    p[0].append(p[2])
    if len(p) == 4:
        p[0] += p[3]


def p_lhs_id(p):
    '''Lhs_id : LV6ID
              | UNDERLINE'''
    p[0] = LeftItemId(cur_scope,p[1].value)


# 自动机和clockblock！会单独开放一个作用域，注意切换当前作用域
# 把return挪到这里面了,这里返回一个填好各项参数的equation，并已经将个子作用域添加到当前作用域中
# return 返回列表。这里要根据情况返回一个equation
# p[1]会返回一个对应的名字
def p_control_block(p):
    'Control_block : State_machine Return'
    global cur_scope
    lhs = cur_scope.get_childScope(p[1]).get_return_symbolTable()
    returned_names = p[2]
    # 检查ruturn的变量是否符合要求，即显示返回的变量里面有没有lhs以外的东西
    for symbol_name in returned_names:
        if symbol_name == "..":  # 遇到这个说明完成了..只会在最后面
            break
        if symbol_name not in lhs.keys():
            # 没有就报错
            raise UnknownIdentifierException(f"{symbol_name}在returned变量中却没有被修改")
    lhs_items=[LeftItemId(cur_scope,id) for id in lhs.keys()]
    p[0] = SyntaxEquation(type="control_block", lhs=lhs_items, lineno=p.lineno(1), scope=cur_scope)
    p[0].controlBlockID = p[1]


def p_clocked_equation(p):
    'Clocked_equation : Clocked_block Return'
    global cur_scope
    lhs = cur_scope.get_childScope(p[1]).get_return_symbolTable()
    returned_names = p[2]
    # 检查ruturn的变量是否符合要求，即显示返回的变量里面有没有lhs以外的东西
    for symbol_name in returned_names:
        if symbol_name == "..":  # 遇到这个说明完成了..只会在最后面
            break
        if symbol_name not in lhs.keys():
            # 没有就报错
            raise UnknownIdentifierException(f"{symbol_name}在returned变量中却没有被修改")
    lhs_items = [LeftItemId(cur_scope, name) for name in lhs.keys()]
    p[0] = SyntaxEquation(type="control_block", lhs=lhs_items, lineno=p.lineno(1), scope=cur_scope)
    p[0].controlBlockID = p[1]


def p_state_machine(p):  # 返回此状态机的名字
    '''State_machine : State_machine_decl
                     | State_machine_decl State_machine_1'''
    global cur_scope
    p[0] = p[1]
    cur_scope = cur_scope.prevScope
    p.set_lineno(0, p.lineno(1))


def p_state_machine_decl(p):  # 切换作用域
    '''State_machine_decl : AUTOMATON
                          | AUTOMATON LV6ID'''
    global cur_scope
    if len(p) == 3:
        name = p[2].value
    else:
        name = cur_scope.generate_name_for_subScope()
    p[0] = name
    scope = SyntaxAutomaton(type="automaton", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p.set_lineno(0, p.lineno(1))


def p_state_machine_1(p):
    '''State_machine_1 : State_decl
                       | State_machine_1 State_decl'''


def p_state_decl(p):  # 一个state就是一个子作用域，注意切换作用域
    '''State_decl : State_decl_core
                  | State_decl_core UNTIL State_decl_6
                  | State_decl_core UNTIL State_decl_6 SYNCHRO Fork SEMICOLON
                  | State_decl_core UNTIL State_decl_6 SYNCHRO Actions Fork SEMICOLON'''
    global cur_scope
    if len(p) == 2:
        cur_scope = cur_scope.prevScope
    elif len(p) == 4:
        cur_scope.set_untilTransitions(p[3])
        cur_scope = cur_scope.prevScope
    elif len(p) == 7:
        cur_scope.set_untilTransitions(p[3])
        cur_scope.set_synchroArrow(p[5])
        cur_scope = cur_scope.prevScope
    else:
        p[6].set_action(p[5])
        cur_scope.set_untilTransitions(p[3])
        cur_scope.set_synchroArrow(p[6])
        cur_scope = cur_scope.prevScope


def p_before_state_data_def(p):  # 切换作用域
    '''Before_state_data_def : STATE State_Lv6id
                             | INITIAL STATE State_Lv6id
                             | FINAL STATE State_Lv6id
                             | INITIAL FINAL STATE State_Lv6id'''
    global cur_scope
    state_name = p[len(p) - 1].value
    state = SyntaxState(type="automaton_state", name=state_name, prevscope=cur_scope, visibility="public")
    state.isInitial = p[1].strs == "initial"
    state.isFinal = any(item.strs == "final" for item in p[1:-1])
    cur_scope.add_childScope(state)
    cur_scope.add_state(state)
    cur_scope = state


def p_state_decl_core(p):
    '''State_decl_core : Before_state_data_def
                       | Before_state_data_def State_data_def
                       | Before_state_data_def UNLESS State_decl_5
                       | Before_state_data_def UNLESS State_decl_5 State_data_def'''
    if len(p) == 4 or len(p) == 5:
        global cur_scope
        transition_index = 3
        cur_scope.set_unlessTransitions(p[transition_index])


def p_state_data_def(p):  # 重写一个data_def，让当前作用域为SyntaxState
    '''State_data_def :  Equation SEMICOLON
                     | Scope'''


def p_state_decl_5(p):
    '''State_decl_5 : Transition SEMICOLON
                    | Transition SEMICOLON State_decl_6'''
    p[0] = list()
    p[0].append(p[1])
    if len(p) == 4:
        p[0] += p[3]


def p_state_decl_6(p):
    '''State_decl_6 : Transition SEMICOLON
                    | State_decl_6 Transition SEMICOLON'''
    p[0] = list()
    if len(p) == 3:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[2])


def p_transition(p):
    '''Transition : IF Expr Arrow'''
    p[0] = list()
    p[0].append(p[2])
    p[0].append(p[3])


def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    p[0] = p[1]


# 一个action就是一个data_def，即使只有emit语句也可以是data_def。
# 若为data_def则已经生成好了作用域不用处理
# 若不为则需要自己生成一个作用域
def p_actions(p):
    '''Actions : DO LBPARENTHESE EMIT Emission_body RPARENTHESE
    | DO LBPARENTHESE Emission_body RPARENTHESE
    | DO LBPARENTHESE EMIT Emission_body Action_tail RPARENTHESE
    | DO LBPARENTHESE Emission_body Action_tail RPARENTHESE
    | Action_data_def'''
    global cur_scope
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = p[2]
    else:
        scope = SyntaxDataDefScope(type="data_def", name=cur_scope.generate_name_for_subScope(), prevscope=cur_scope,
                                   visibility="public")
        cur_scope.add_childScope(scope)
        if p[3].strs == "emit":
            emission_index = 4
            tail_index = 5 if len(p) == 8 else None
        else:
            emission_index = 3
            tail_index = 4 if len(p) == 7 else None
            p[emission_index].emit = False
        scope.add_equation(p[emission_index])
        for equation in p[tail_index] if tail_index is not None else []:
            scope.add_equation(equation)
        p[0] = scope.name
        # 不切换作用域，直接新建一个作用域塞到当前作用域里就可以了
    # 更新一下当前作用域的返回值列表，将actions的返回值列表并入state内
    # 给当前state加一个记录action的作用域

    action_scope = cur_scope.get_childScope(p[0])
    cur_scope.add_action_subscope(action_scope)
    cur_scope.returnSymbolsTable.update(action_scope.returnSymbolsTable)


def p_action_tail(p):
    '''Action_tail : SEMICOLON EMIT Emission_body
                   | SEMICOLON Emission_body
                   | Action_tail SEMICOLON EMIT Emission_body
                   | Action_tail SEMICOLON Emission_body'''
    p[0] = list()
    if len(p) == 4:
        p[0].append(p[3])
    elif len(p) == 3:
        p[2].emit = False
        p[0].append(p[2])
    elif p[3].strs == "emit":
        p[0] += p[1]
        p[0].append(p[4])
    else:
        p[3].emit = False
        p[0] += p[1]
        p[0].append(p[3])


def p_arrow(p):  # 给arrow添加actions并返回
    '''Arrow : DO Target
    | Actions Fork
    | Fork'''
    global cur_scope
    if isinstance(p[1], lex_value) and p[1].strs == "do":
        p[0] = SyntaxArrow(type=p[2]["type"], state=cur_scope, target=p[2]["target"])
    elif len(p) != 2:
        p[2].set_action(p[1])
        p[0] = p[2]
    else:
        # 这里生成一个空data_def
        scope = SyntaxDataDefScope(type="data_def", name=cur_scope.generate_name_for_subScope(),
                                   prevscope=cur_scope,
                                   visibility="public")
        cur_scope.add_childScope(scope)
        cur_scope.add_action_subscope(scope)
        p[1].set_action(scope.name)
        p[0] = p[1]





def p_fork(p):  # 在这里就创建一个arrow对象
    '''Fork : Target
    | IF Expr Arrow END
    | IF Expr Arrow ELSE Arrow END
    | IF Expr Arrow Fork_1 END
    | IF Expr Arrow Fork_1 ELSE Arrow END'''
    if len(p) == 2:
        p[0] = SyntaxArrow(type=p[1]["type"], state=cur_scope, target=p[1]["target"])
    else:
        ifList = list()
        ifList.append([p[2], p[3]])
        if len(p) == 5:
            else_expr = None
        elif len(p) == 6:
            ifList += p[4]
            else_expr = None
        elif len(p) == 7:
            else_expr = p[5]
        else:
            ifList += p[4]
            else_expr = p[6]
        p[0] = SyntaxArrow(type="if", state=cur_scope,ifExpr=ifList, elseExpr=else_expr)


def p_fork_1(p):
    '''Fork_1 : Elsif_fork
              | Fork_1 Elsif_fork'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[2])


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
    '''Clocked_block : Match_clocked_header Match_block
     | If_clocked_header If_block'''
    global cur_scope
    cur_scope.block = p[2]
    cur_scope = cur_scope.prevScope
    p[0] = p[1]
    p.set_lineno(0, p.lineno(1))


def p_match_clocked_header(p):
    '''Match_clocked_header : ACTIVATE
                            | ACTIVATE LV6ID'''
    global cur_scope
    if len(p) == 2:
        name = cur_scope.generate_name_for_subScope()
    else:
        name = p[2].value
    scope = SyntaxClockedScope(type="match_block", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p[0] = name
def p_match_block(p):
    '''Match_block : WHEN Expr MATCH Match_block_1'''
    p[0] = SyntaxMatchBlock(expr=p[2], matchList=p[4],scope=cur_scope)


def p_match_block_1(p):
    '''Match_block_1 : VERTICALBAR Pattern Match_data_def
                     | Match_block_1 VERTICALBAR Pattern Match_data_def'''
    p[0] = list()
    if len(p) == 4:
        tmp = [p[2], p[3]]
    else:
        p[0] += p[1]
        tmp = [p[3], p[4]]
    p[0].append(tmp)


def p_match_data_def(p):
    '''Match_data_def : Match_data_def_start Data_def_body'''
    p[0] = leave_data_def_scope(p[1])


def p_match_data_def_start(p):
    'Match_data_def_start : COLON'
    p[0] = enter_data_def_scope()


def p_if_clocked_header(p):
    '''If_clocked_header : ACTIVATE
                         | ACTIVATE LV6ID'''
    global cur_scope
    if len(p) == 2:
        name = cur_scope.generate_name_for_subScope()
    else:
        name = p[2].value
    scope = SyntaxClockedScope(type="if_block", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    p[0] = name


def p_if_block(p):
    'If_block : IF Expr Then_clause Else_clause'
    p[0] = SyntaxIfBlock(expr=p[2], thenBlock=p[3], elseBlock=p[4],scope=cur_scope)


def p_then_clause(p):
    '''Then_clause : Then_data_def
                   | THEN If_block'''
    p[0] = p[1] if len(p) == 2 else p[2]


def p_then_data_def(p):
    '''Then_data_def : Then_data_def_start Data_def_body'''
    p[0] = leave_data_def_scope(p[1])


def p_then_data_def_start(p):
    'Then_data_def_start : THEN'
    p[0] = enter_data_def_scope()


def p_else_clause(p):
    '''Else_clause : Else_data_def
                   | ELSE If_block'''
    p[0] = p[1] if len(p) == 2 else p[2]


def p_else_data_def(p):
    '''Else_data_def : Else_data_def_start Data_def_body'''
    p[0] = leave_data_def_scope(p[1])


def p_else_data_def_start(p):
    'Else_data_def_start : ELSE'
    p[0] = enter_data_def_scope()


# return返回值，返回ID列表,包括..的情况，在equation层进行处理
def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0] = p[2]


def p_returns_var(p):
    '''Returns_var : Returns_var_2
                   | Returns_var_1 Returns_var_2'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
        return
    p[0] += p[1]
    if p[2] in p[1]:
        # 重复定义，报错
        raise MultipleFlowDefinitionException(p[2])
    else:
        p[0].append(p[2])


def p_returns_var_1(p):
    '''Returns_var_1 : LV6ID COMMA
                      | Returns_var_1 LV6ID COMMA'''
    p[0] = list()
    if len(p) == 3:
        p[0].append(p[1].value)
    else:
        p[0] += p[1]
        if p[2].value in p[1]:
            raise MultipleFlowDefinitionException(p[2].value)
        p[0].append(p[2].value)


def p_returns_var_2(p):
    '''Returns_var_2 : LV6ID
    | TPOINT'''
    p[0] = p[1].value


def enter_data_def_scope():
    global cur_scope
    name = cur_scope.generate_name_for_subScope()
    scope = SyntaxDataDefScope(type="data_def", name=name, prevscope=cur_scope, visibility="public")
    cur_scope.add_childScope(scope)
    cur_scope = scope
    return name


def leave_data_def_scope(name):
    global cur_scope
    cur_scope = cur_scope.prevScope
    return name


def p_action_data_def(p):
    '''Action_data_def : Action_data_def_start Data_def_body'''
    p[0] = leave_data_def_scope(p[1])


def p_action_data_def_start(p):
    'Action_data_def_start : DO'
    p[0] = enter_data_def_scope()


def p_data_def_body(p):
    '''Data_def_body : Equation SEMICOLON
                     | Scope'''


def p_scope(p):
    '''Scope : Eqs
             | Signal_block_local_block Eqs
             | Signal_block_local_block'''


def p_eqs(p):
    '''Eqs : LET TEL
           | LET Eqs_item_list TEL
           | LET Clocked_equation TEL'''


def p_eqs_item_list(p):
    '''Eqs_item_list : Equation SEMICOLON
                     | Eqs_item_list Equation SEMICOLON'''

d=dict()
def make_list_expr(values):
    return expression_factory(type="List_expr", sub_type="List_expr", scope=cur_scope, objects=[values])

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
    _type=p[0].type+"_"+p[0].subType
    if d.get(_type) is None:
        d[_type]=1
    else:
        d[_type]+=1


def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    if len(p) == 2:
        p[0] = expression_factory(type="Id_expr", sub_type="Path_id",scope=cur_scope,objects=[p[1].value])
    elif len(p) == 3:
        p[0] = expression_factory(type="Id_expr", sub_type="singlequoteLv6id",scope=cur_scope,objects=[p[1].value + p[2].value])
    elif len(p) == 4:
        p[0] = expression_factory(type="Id_expr", sub_type="lastSinglequoteLv6id",scope=cur_scope,objects=[p[2].value + p[3].value])
        # 为什么我要在这里把'加上？？现在删不掉了

def p_atom(p):
    '''Atom : Bool_atom
    | INTEGERNUM
    | FLOATNUM
    | CHARACTER
    | TYPED_INTEGER
    | TYPED_FLOAT'''
    if p[1].strs == 'true' or p[1].strs == 'false':
        p[0] = expression_factory(type="Atom", sub_type="bool_atom",scope=cur_scope,objects=[p[1].value])
    else:
        p[0] = expression_factory(type="Atom", sub_type=p[1].strs,scope=cur_scope,objects=[p[1].value])


def p_tempo_expr(p):
    '''Tempo_expr : Expr ARROW Expr
    | PRE Expr
    | FBY LPARENTHESE Nonempty_expr_list SEMICOLON Expr SEMICOLON Nonempty_expr_list RPARENTHESE
    | FBY LPARENTHESE SEMICOLON Expr SEMICOLON Nonempty_expr_list RPARENTHESE
    | FBY LPARENTHESE Nonempty_expr_list SEMICOLON Expr SEMICOLON RPARENTHESE
    | FBY LPARENTHESE SEMICOLON Expr SEMICOLON RPARENTHESE
    | Expr TIMES Expr
    | Expr WHEN Clock_expr
    | MERGE LPARENTHESE Expr SEMICOLON Merge_case_list RPARENTHESE'''
    global cur_scope
    if len(p) == 3:
        p[0] = expression_factory(type="Tempo_expr", sub_type="PRE",scope=cur_scope,objects=[p[2]])
    elif len(p) == 4:
        if p[2].strs == "->":
            p[0] = expression_factory(type="Tempo_expr", sub_type="ARROW",scope=cur_scope,objects=[p[1],p[3]])
        elif p[2].strs == "times":
            # 适配prefixop的形式
            p[0] = expression_factory(type="Tempo_expr", sub_type="TIMES",scope=cur_scope,objects=[[p[1],p[3]]])
        elif p[2].strs == "when":
            p[0] = expression_factory(type="Tempo_expr", sub_type="WHEN",scope=cur_scope,objects=[p[1],p[3]])
    elif p[1].strs == "fby":
        if p.slice[3].type == "SEMICOLON":
            left = make_list_expr([])
            expr = p[4]
            right = make_list_expr(p[6])
        elif len(p) == 8:
            left = make_list_expr(p[3])
            expr = p[5]
            right = make_list_expr([])
        else:
            left = make_list_expr(p[3])
            expr = p[5]
            right = make_list_expr(p[7])
        p[0] = expression_factory(type="Tempo_expr", sub_type="FBY",scope=cur_scope,objects=[left,expr,right])
    elif p[1].strs == "merge":
        p[0] = expression_factory(type="Tempo_expr", sub_type="MERGE",scope=cur_scope,objects=[p[3],p[5]])


def p_merge_case_list(p):
    '''Merge_case_list : Merge_case
                       | Merge_case_list SEMICOLON Merge_case'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_merge_case(p):
    'Merge_case : Nonempty_expr_list'
    p[0] = make_list_expr(p[1])


def p_arith_expr(p):
    '''Arith_expr : LPARENTHESE Expr COLON Type_expr RPARENTHESE'''
    p[0] = expression_factory(type="Arith_expr", sub_type="cast",scope=cur_scope,objects=[p[2],p[4]])


def p_arith_expr_unary(p):
    '''Arith_expr : MINUS Expr %prec UMINUS
    | PLUS Expr %prec UPLUS
    | LNOT Expr'''
    p[0] = expression_factory(type="Arith_expr", sub_type="unary",scope=cur_scope,objects=[p[1].value,p[2]])

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
    p[0] = expression_factory(type="Arith_expr", sub_type="binOp",scope=cur_scope,objects=[[p[1],p[3]],p[2].value])


def p_relation_expr(p):
    '''Relation_expr : Expr EQU Expr
    | Expr NOEQU Expr
    | Expr LESS Expr
    | Expr GREATER Expr
    | Expr LESSEQU Expr
    | Expr GREATEREQU Expr'''
    p[0] = expression_factory(type="Relation_expr", sub_type="Relation_expr",scope=cur_scope,objects=[[p[1],p[3]],p[2].value])

def p_list_expr(p):
    '''List_expr : LPARENTHESE RPARENTHESE
                 | LPARENTHESE Nonempty_expr_list RPARENTHESE'''
    values = [] if len(p) == 3 else p[2]
    p[0] = expression_factory(type="List_expr", sub_type="List_expr", scope=cur_scope, objects=[values])


def p_nonempty_expr_list(p):
    '''Nonempty_expr_list : Expr
                          | Nonempty_expr_list COMMA Expr'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[3])


def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr
    | LPARENTHESE CASE Expr OF Switch_expr_1 RPARENTHESE'''
    if p[1].strs == "if":
        list_expr = expression_factory("List_expr", "List_expr", cur_scope, [[p[2], p[4], p[6]]])
        p[0] = expression_factory(type="Switch_expr", sub_type="IF",scope=cur_scope,objects=[list_expr])
    else:
        p[0] = expression_factory(type="Switch_expr", sub_type="CASE",scope=cur_scope,objects=[p[3],p[5]])


def p_switch_expr_1(p):
    '''Switch_expr_1 : Case_expr
                     | Switch_expr_1 Case_expr'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[2])


def p_case_expr(p):
    'Case_expr : VERTICALBAR Pattern COLON Expr'
    p[0] = list()
    p[0].append(p[2])
    p[0].append(p[4])


def p_bool_expr(p):
    '''Bool_expr : NOT Expr
    | HASHTAG LPARENTHESE RPARENTHESE
    | HASHTAG LPARENTHESE Nonempty_expr_list RPARENTHESE'''
    if len(p) == 3:
        p[0] = expression_factory(type="Bool_expr", sub_type="NOT",scope=cur_scope,objects=[p[2]])
    else:
        values = [] if len(p) == 4 else p[3]
        p[0] = expression_factory(type="Bool_expr", sub_type="HASHTAG",scope=cur_scope,objects=[values])


def p_bool_expr_bin(p):
    '''Bool_expr : Expr AND Expr
    | Expr OR Expr
    | Expr XOR Expr'''
    p[0] = expression_factory(type="Bool_expr", sub_type="binOp",scope=cur_scope,objects=[[p[1],p[3]],p[2].value])

def p_struct_expr(p):
    '''Struct_expr : Expr POINT LV6ID
    | LBPARENTHESE Label_expr RBPARENTHESE
    | LBPARENTHESE Label_expr Struct_expr_1 RBPARENTHESE'''
    if len(p) == 4:
        if isinstance(p[1], lex_value):
            labels = {p[2][0]: p[2][1]}
            p[0] = expression_factory(type="Struct_expr", sub_type="construct",scope=cur_scope,objects=[labels])
        else:
            p[0] = expression_factory(type="Struct_expr", sub_type="get",scope=cur_scope,objects=[p[1],p[3].value])
    else:
        labels = dict()
        labels[p[2][0]]=p[2][1]
        for label in p[3]:
            labels[label[0]]=label[1]
        p[0] = expression_factory(type="Struct_expr", sub_type="construct",scope=cur_scope,objects=[labels])


def p_struct_expr_1(p):
    '''Struct_expr_1 : COMMA Label_expr
                     | Struct_expr_1 COMMA Label_expr'''
    p[0] = list()
    if len(p) == 3:
        p[0].append(p[2])
    else:
        p[0] += p[1]
        p[0].append(p[3])


def p_label_expr(p):
    '''Label_expr : LV6ID COLON Expr'''
    p[0] = list()
    p[0].append(p[1].value)
    p[0].append(p[3])


def p_array_expr(p):
    '''Array_expr : LBRACKET RBRACKET
    | LBRACKET Nonempty_expr_list RBRACKET
    | Expr Index'''
    if p.slice[1].type == "LBRACKET" and len(p) == 3:
        p[0] = expression_factory(type="Array_expr", sub_type="list",scope=cur_scope,objects=[make_list_expr([])])
    elif p.slice[1].type == "LBRACKET":
        p[0] = expression_factory(type="Array_expr", sub_type="list",scope=cur_scope,objects=[make_list_expr(p[2])])
    else:
        p[0] = expression_factory(type="Array_expr", sub_type="get",scope=cur_scope,objects=[p[1],p[2]])


def p_array_expr2(p):
    '''Array_expr : REVERSE Expr
    | Expr AT Expr'''
    if len(p) == 3:
        p[0] = expression_factory(type="Array_expr", sub_type="reverse",scope=cur_scope,objects=[p[2]])
    else:
        p[0] = expression_factory(type="Array_expr", sub_type="at",scope=cur_scope,objects=[p[1],p[3]])


def p_array_expr3(p):
    '''Array_expr : Expr EXPONENT Expr
    | Expr LBRACKET Expr TPOINT Expr RBRACKET'''
    if len(p) == 4:
        p[0] = expression_factory(type="Array_expr", sub_type="construct",scope=cur_scope,objects=[p[1],p[3]])
    else:
        p[0] = expression_factory(type="Array_expr", sub_type="slice",scope=cur_scope,objects=[p[1],p[3],p[5]])


def p_array_expr4(p):
    '''Array_expr : LPARENTHESE Expr POINT Array_expr_1 DEFAULT Expr RPARENTHESE
    | TRANSPOSE LPARENTHESE Expr SEMICOLON INTEGERNUM SEMICOLON INTEGERNUM RPARENTHESE'''
    if len(p) == 8:
        p[0] = expression_factory(type="Array_expr", sub_type="getdefault",scope=cur_scope,objects=[p[2],p[4],p[6]])
    else:
        p[0] = expression_factory(type="Array_expr", sub_type="transpose",scope=cur_scope,objects=[p[3],p[5].value,p[7].value])


def p_array_expr_1(p):
    '''Array_expr_1 : Index
                    | Array_expr_1 Index'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[2])


def p_label_or_index(p):
    '''Label_or_index : POINT LV6ID
    | Index'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0]=p[2].value

def p_index(p):
    '''Index : LBRACKET Expr RBRACKET'''
    p[0] = p[2]


def p_apply_expr(p):
    '''Apply_expr : Operator LPARENTHESE RPARENTHESE
                  | Operator LPARENTHESE Nonempty_expr_list RPARENTHESE'''
    values = [] if len(p) == 4 else p[3]
    p[0] = expression_factory("Operator","Apply_expr",cur_scope,[p[1],make_list_expr(values)])

    cur_scope.get_my_op_or_state().add_apply_expr(p[0])

op_d=dict()
it_d=dict()
def p_operator(p):
    '''Operator : Prefix
    | LPARENTHESE Prefix LSHIFT RSHIFT RPARENTHESE
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
        objects=[p[1].value,[]]
        if p[1].strs == "path_id":
            p[0] = expression_factory(type="Operator",sub_type="Path_id",scope=cur_scope,objects=objects)
        else:
            p[0] = expression_factory(type="Operator",sub_type="PREFIXOP",scope=cur_scope,objects=objects)
    elif length == 6:
        p[0] = expression_factory(type="Operator",sub_type="PREFIXOP",scope=cur_scope,
                                  objects=[p[2].value,[]])
    elif length == 5:
        if p[2].strs == "make":
            p[0] = expression_factory(type="Operator",sub_type="make",scope=cur_scope,objects=[p[3].value])
        elif p[2].strs == "flatten":
            p[0] = expression_factory(type="Operator",sub_type="flatten",scope=cur_scope,objects=[p[3].value])
    elif length == 7:
        if p[2].value == "activate":
            p[0] = expression_factory(type="Operator",sub_type="activate",scope=cur_scope,objects=[p[3],p[5]])
        elif p[2].value == "restart":
            p[0] = expression_factory(type="Operator",sub_type="restart",scope=cur_scope,objects=[p[3],p[5]])
        else:
            objects=[p[2].value,p[4]]
            if p[2].strs == "path_id":
                p[0] = expression_factory(type="Operator",sub_type="Path_id",scope=cur_scope,objects=objects)
            else:
                p[0] = expression_factory(type="Operator",sub_type="PREFIXOP",scope=cur_scope,objects=objects)

    elif length == 8:
        p[0] = expression_factory(type="Operator",sub_type="iterator",scope=cur_scope,objects=[p[2][0],p[2][1],p[3],p[5]])
    elif length == 9:
        p[0] = expression_factory(type="Operator",sub_type="activateDefault",scope=cur_scope,objects=[p[3],p[5],p[7]])
    elif length == 10:

        if p[2].strs == "activate":
            objects = [p[3], p[5], p[8]]
            p[0] = expression_factory(type="Operator",sub_type="activateInitDefault",scope=cur_scope,objects=objects)
        else:
            objects=[p[2].strs,1,p[3],p[5],p[8]]
            p[0] = expression_factory(type="Operator",sub_type="iterator_mw",scope=cur_scope,objects=objects)
    elif length == 12:
        p[0] = expression_factory(type="Operator",sub_type="iterator_mw",scope=cur_scope,
                                  objects=[p[2][0],p[2][1],p[3],p[5],p[8],p[10]])

    t=p[0].subType
    if t not in op_d:
        op_d[t]=0
    op_d[t]+=1

    if t=="iterator_mw" or t=="iterator":
        it=p[0].objects[0]
        if it not in it_d:
            it_d[it]=0
        it_d[it]+=1


def p_prefix(p):
    '''Prefix : Path_id
    | PREFIXOP'''
    p[0] = p[1]
    if p[1].strs == "path_id":
        # 让此句所处的函数级作用域添加此路径作为依赖的函数
        global cur_scope
        user_op=cur_scope.get_my_userOp()
        user_op.add_dependent_function(p[1].value)


def p_operator_1(p):
    '''Operator_1 : Expr
                  | Operator_1 COMMA Expr'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[3])


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
        p[0] = [p[1].value,1]
    else:
        p[0] = [p[1].value,int(p[2].value)]


def p_iterator_mw(p):
    '''Iterator_mw : MAPW
    | MAPWI
    | MAPFOLDW
    | MAPFOLDW INTEGERNUM
    | MAPFOLDWI
    | MAPFOLDWI INTEGERNUM'''
    if len(p) == 2:
        p[0] = [p[1].value,1]
    else:
        p[0] = [p[1].value,int(p[2].value)]


def p_mixed_constructor(p):
    '''Mixed_constructor : LPARENTHESE Expr WITH Mixed_constructor_1 EQU Expr RPARENTHESE'''
    p[0] = expression_factory(type="Mixed_constructor", sub_type="Mixed_constructor",scope=cur_scope,objects=[p[2],p[4],p[6]])


def p_mixed_constructor_1(p):
    '''Mixed_constructor_1 : Label_or_index
                           | Mixed_constructor_1 Label_or_index'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1])
    else:
        p[0] += p[1]
        p[0].append(p[2])


# 变量声明
# 返回一个SyntaxVariableSymbol的列表，不更新到符号表之中
def p_var_decls(p):
    '''Var_decls : Var_id COLON Type_expr
                 | Var_id Var_decls_1 COLON Type_expr
                 | Var_id COLON Type_expr Var_decl_suffix
                 | Var_id Var_decls_1 COLON Type_expr Var_decl_suffix'''
    var_id_list = [p[1]]
    if isinstance(p[2], list):
        var_id_list += p[2]
        type_index = 4 if len(p) == 6 else 4
        suffix = p[5] if len(p) == 6 else None
    else:
        type_index = 3
        suffix = p[4] if len(p) == 5 else None
    for var_id in var_id_list:
        var_id.syntaxType = p[type_index]
        if suffix is not None:
            if suffix["when"] is not None:
                var_id.whenExpr = suffix["when"]
            if suffix["default"] is not None:
                var_id.defaultExpr = suffix["default"]
            if suffix["last"] is not None:
                var_id.lastExpr = suffix["last"]
    p[0] = var_id_list


def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | COMMA Var_id'''
    p[0] = list()
    p[0].append(p[2])
    if len(p) == 4:
        p[0] += p[3]


def p_var_id(p):
    '''Var_id : LV6ID
              | CLOCK LV6ID
              | PROBE LV6ID
              | CLOCK PROBE LV6ID
              | PROBE CLOCK LV6ID'''
    if len(p) == 2:
        is_clock = False
        is_probe = False
        name = p[1].value
    else:
        modifiers = [item.strs for item in p[1:-1]]
        is_clock = "clock" in modifiers
        is_probe = "probe" in modifiers
        name = p[len(p) - 1].value
    p[0] = SyntaxVariableSymbol(name=name, isClock=is_clock, isProbe=is_probe,scope=cur_scope)


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
    p[0] = SyntaxClockExpr(ID=ID, type=type,scope=cur_scope)
    if len(p) == 6:
        p[0].pattern = p[4]


# 返回SyntaxPattern
def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | INTEGERNUM
    | MINUS INTEGERNUM
    | TYPED_INTEGER
    | MINUS TYPED_INTEGER
    | Bool_atom
    | UNDERLINE'''
    if len(p) == 3:
        _type = p[2].strs
        value = p[1].value + p[2].value
    else:
        value = p[1].value
        _type = p[1].strs
    p[0] = SyntaxPattern(_type=_type, value=value,scope=cur_scope)


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    p[0] = p[1]


def p_var_decl_suffix(p):
    '''Var_decl_suffix : When_decl
                       | Default_decl
                       | Last_decl
                       | When_decl Default_decl
                       | When_decl Last_decl
                       | Default_decl Last_decl
                       | When_decl Default_decl Last_decl'''
    p[0] = {"when": None, "default": None, "last": None}
    for index in range(1, len(p)):
        option_type = p.slice[index].type
        if option_type == "When_decl":
            p[0]["when"] = p[index]
        elif option_type == "Default_decl":
            p[0]["default"] = p[index]
        elif option_type == "Last_decl":
            p[0]["last"] = p[index]


def p_default_decl(p):
    '''Default_decl : DEFAULT EQU Expr'''
    p[0] = p[3]


def p_last_decl(p):
    '''Last_decl : LAST EQU Expr'''
    p[0] = p[3]


# ID 返回列表，存储每个ID
def p_id_one_or_more_with_comma(p):
    '''Id_one_or_more_with_comma : LV6ID
                                 | Id_one_or_more_with_comma COMMA LV6ID'''
    p[0] = list()
    if len(p) == 2:
        p[0].append(p[1].value)
    else:
        p[0] += p[1]
        p[0].append(p[3].value)


# path_id，返回lex_value，path只搜索package！
def p_path_id(p):
    '''Path_id : LV6ID
               | LV6ID Path_1'''
    p[0] = lex_value("path_id", "")
    p[0].value += p[1].value
    if len(p) == 3:
        p[0].value += p[2].value


def p_path_1(p):
    '''Path_1 : DOUBLECOLON LV6ID Path_1
    | DOUBLECOLON LV6ID'''
    p[0] = lex_value("path_1", "")
    p[0].value += p[1].value + p[2].value
    if len(p) == 4:
        p[0].value += p[3].value


# 模板id 返回lex_value
def p_typevar(p):
    '''Typevar : SINGLEQUOTE LV6ID'''
    p[0] = lex_value("typevar", p[1].value + p[2].value)


def p_external(p):
    'External : IMPORTED'
    p[0] = dict()
    p[0]["External"] = p[1].value


def p_visibility(p):
    '''Visibility : PRIVATE
    | PUBLIC'''
    p[0] = dict()
    p[0]["Visibility"] = p[1].value


def p_error(p):
    raise Exception(f"lex error: {p} at line {p.lineno}")
    # print("error", p)


def get_parse(input_path: str, root_operator: str):
    parser = yacc(debug=1, start="Program")

    with open(input_path, 'rb') as f:
        data=f.read()
        encoding = chardet.detect(data)['encoding']
    with open(input_path,"r",encoding=encoding) as f:
        strs = f.read()

    strs = re.sub(r'(?s)#pragma\b.*?#end\b\s*','',strs,flags=re.DOTALL)
    strs = re.sub( r'--.*?$', '', strs,flags=re.MULTILINE)
    pattern1 = r'%[a-zA-Z0-9_!"$#%&\'()*+,\-./:;_<=>?@\\^`|{}~\s]*?%'
    strs = re.sub(pattern1, '', strs, flags=re.MULTILINE)
    pattern2 = r'\(\*.*?\*\)'
    strs = re.sub(pattern2,'',strs,flags=re.DOTALL)
    strs = re.sub(r'#[A-Za-z0-9_]+','',strs)

    # pattern3 = re.compile(r'\*.*?\*',flags=re.MULTILINE)
    # strs = re.sub(pattern3, '', strs)
    pattern4 = r'(?s)/\*.*?\*/'
    strs = re.sub(pattern4,"",strs)
    print("=======strs=====\n", strs)
    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)
    return root_scope


if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-r', '--root_operator', required=True, type=str)
    args = argParser.parse_args()
    get_parse(args.input_path, args.root_operator)
