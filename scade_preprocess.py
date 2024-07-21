import copy
import inspect
from ply.yacc import yacc
# from scade_lex import scade_lex, get_tokens, tokens, lex_value
import re
from scade_compile_otherFunc import *

class graphTree:
    def __init__(self,Name = "",Type= ""):
        self.name = Name
        self.preNode=None
        self.type = Type #root,package,node,applyFunc
        self.son=list()
    
def traversal(graphTree,path,strList):
    print("traversal path=",path," name=",graphTree.name," graphTree.type=",graphTree.type," len=",len(graphTree.son))
    if graphTree.name != "" and graphTree.type != 'applyFunc':
        path.append(graphTree.name)
    if graphTree.type == 'applyFunc':
        str="\""+'::'.join(path)+"\""
        str+="-> \"%s\";"%(graphTree.name)
        strList.add(str)
        return
    else:
        for elem in graphTree.son:
            traversal(elem,path,strList)
        if len(path)!=0:
            path.pop()
    

def writeFile(node):
    path=list()
    strList=set()    
    traversal(node,path,strList)
    str="digraph{\n"
    for elem in strList:
        str+="%s\n"%elem
    str+="}"
    file=open("test_aircraft_brake_system.dot",'w')
    file.write(str)
    print("======dot file=====\n")
    print(str)

programNode=graphTree("","root")
curNode=programNode

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

def p_program(p):
    'Program : Decls_zero_or_more'
    pass 

def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''
    pass


def p_decls(p):
    '''Decls : Const_block
    | Type_block
    | Sensor_block
    | Package_decl
    | User_op_decl
    | Group_block
    | OPEN Path_id'''
    #TODO:group_block和open path 
    pass

def p_group_block(p):
    '''Group_block : GROUP Group_block_1'''
    pass

def p_group_block_1(p):
    '''Group_block_1 : Group_decl SEMICOLON Group_block_1
                     | empty'''
    pass

def p_group_decl(p):
    '''Group_decl : Visibility_zero_or_one LV6ID EQU Group_expr'''
    pass

def p_group_expr(p):
    '''Group_expr : LPARENTHESE Type_expr Group_expr_1 RPARENTHESE'''
    pass

def p_group_expr_1(p):
    '''Group_expr_1 : COMMA Type_expr Group_expr_1
                    | empty'''
    pass


def p_type_block(p):
    'Type_block : TYPE Type_block_1'
    pass


def p_type_block_1(p):
    '''Type_block_1 : Type_decl SEMICOLON Type_block_1
                    | empty'''
    pass


def p_Type_decl(p):
    'Type_decl : Interface_status LV6ID Type_decl_1 Type_decl_2'
    pass


def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    pass


def p_type_decl_2(p):
    '''Type_decl_2 : IS Numeric_kind
                   | empty'''
    pass


def p_type_def(p):
    '''Type_def : Type_expr
                | ENUM LBPARENTHESE Id_one_or_more_with_comma RBPARENTHESE'''
    pass


def p_numeric_kind(p):
    '''Numeric_kind : NUMERIC
    | FLOAT
    | INTEGER
    | SIGNED
    | UNSIGNED'''
    pass


def p_package_decl(p):
    'Package_decl : Package Visibility_zero_or_one Pack_Lv6id Decls_zero_or_more END SEMICOLON'
    global curNode
    curNode=curNode.pre

def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    global curNode
    curNode=curNode.pre


def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0]=p[1]
    global curNode
    node=graphTree(p[1].value,"package")
    node.pre=curNode
    curNode.son.append(node)
    curNode=node
    print("this package is ",p[1].value)


def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
    global curNode
    node=graphTree(p[1].value,"node")
    node.pre=curNode
    curNode.son.append(node)
    curNode=node
    print("this node is ",p[1].value)


def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    pass


def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    pass


def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL'''
    pass


def p_signal_block_zero_or_one(p):
    '''Signal_block_zero_or_one : Signal_block
    | empty'''
    pass

def p_signal_block(p):
    'Signal_block : SIG Id_one_or_more_with_comma SEMICOLON'
    pass

def p_local_block_zero_or_one(p):
    '''Local_block_zero_or_one : Local_block
    | empty'''
    pass


def p_local_block(p):
    '''Local_block : VAR Local_block_1
    | empty'''
    pass


def p_local_block_1(p):
    '''Local_block_1 : Var_decls SEMICOLON Local_block_1
    | empty'''
    pass


def p_equation_zero_or_more_with_semicolon(p):
    '''Equation_zero_or_more_with_semicolon : Equation SEMICOLON Equation_zero_or_more_with_semicolon
    | empty'''
    pass


def p_equation(p):
    '''Equation : Simple_equation
                | Assert
                | Control_block Return
                | Emission'''
    #TODO:Emission未完成
    pass

def p_emission(p):
    '''Emission : EMIT Emission_body'''
    #TODO:not finish
    pass

def p_emission_body(p):
    '''Emission_body : SINGLEQUOTE LV6ID Emission_body_1
                    | LPARENTHESE SINGLEQUOTE LV6ID Emission_body_2 RPARENTHESE Emission_body_1'''
    #TODO:not finish
    pass

def p_emission_body_1(p):
    '''Emission_body_1 : IF Expr
                        | empty'''
    #TODO:not finish
    pass

def p_emission_body_2(p):
    '''Emission_body_2 : COMMA SINGLEQUOTE Emission_body_2
                        | empty'''
    pass

def p_assert(p):
    '''Assert : ASSUME LV6ID COLON Expr
            | GUARANTEE LV6ID COLON Expr'''
    pass


def p_control_block(p):
    '''Control_block : State_machine
    | Clocked_block'''
    pass


def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0] = lex_value("Return")
    pass

def p_returns_var(p):
    '''Returns_var : Returns_var_1 Returns_var_2'''
    pass


def p_returns_var_1(p):
    '''Returns_var_1 : Returns_var_1 LV6ID COMMA
    | empty'''
    pass


def p_returns_var_2(p):
    '''Returns_var_2 : LV6ID
    | TPOINT'''
    pass


def p_state_machine(p):
    '''State_machine : AUTOMATON Id_zero_or_one State_machine_1'''
    pass


def p_state_machine_1(p):
    '''State_machine_1 : State_decl State_machine_1
                       | empty'''
    pass


def p_state_decl(p):
    '''State_decl : State_decl_1 State_decl_2 STATE State_Lv6id State_decl_3 Data_def State_decl_4'''
    pass


def p_state_decl_1(p):
    '''State_decl_1 : INITIAL
                    | empty'''
    pass


def p_state_decl_2(p):
    '''State_decl_2 : FINAL
                    | empty'''
    pass


def p_state_decl_3(p):
    '''State_decl_3 : UNLESS State_decl_5
    | empty'''
    pass

def p_state_decl_5(p):
    '''State_decl_5 : Transition SEMICOLON State_decl_6'''
    pass

def p_state_decl_6(p):
    '''State_decl_6 : Transition SEMICOLON State_decl_6
    | empty'''

def p_data_def(p):
    '''Data_def : Equation SEMICOLON
                | Scope'''
    pass


def p_scope(p):
    '''Scope : Signal_block_zero_or_one Local_block_zero_or_one Eqs
    | Signal_block_zero_or_one Local_block_zero_or_one'''
    #未完成
    pass


def p_eqs(p):
    'Eqs : LET Equation_zero_or_more_with_semicolon TEL'
    pass


def p_state_decl_4(p):
    '''State_decl_4 : UNTIL State_decl_6 State_decl_7
                    | empty '''
    pass

def p_state_decl_7(p):
    '''State_decl_7 : SYNCHRO State_decl_8 Fork SEMICOLON
    | empty'''
    pass

def p_state_decl_8(p):
    '''State_decl_8 : Actions
    | empty'''
    pass

def p_transition(p):
    '''Transition : IF Expr Arrow'''
    pass

def p_arrow(p):
    '''Arrow : Actions Fork
    | Fork'''
    pass

def p_fork(p):
    '''Fork : Target
    | IF Expr Arrow Fork_1 Fork_2 END'''
    pass

def p_fork_1(p):
    '''Fork_1 : Elsif_fork Fork_1
    | empty'''
    pass

def p_fork_2(p):
    '''Fork_2 : Else_fork
    | empty'''
    pass

def p_elsif_fork(p):
    '''Elsif_fork : ELSIF Expr Arrow'''
    pass

def p_else_fork(p):
    '''Else_fork : ELSE Arrow'''
    pass

def p_target(p):
    '''Target : RESTART LV6ID
    | RESUME LV6ID'''
    pass

def p_actions(p):
    '''Actions : DO LBPARENTHESE Actions_1 Emission_body Actions_2 RBPARENTHESE
    | DO Data_def'''
    pass

def p_actions_1(p):
    '''Actions_1 : EMIT
    | empty'''
    pass

def p_actions_2(p):
    '''Actions_2 : SEMICOLON Actions_1 Emission_body Actions_2
    | empty'''
    pass

def p_clocked_block(p):
    '''Clocked_block : ACTIVATE Id_zero_or_one If_block
    | ACTIVATE Id_zero_or_one Match_block'''
    pass

def p_id_zero_or_one(p):
    '''Id_zero_or_one : LV6ID
    | empty'''
    pass


def p_if_block(p):
    'If_block : IF Expr THEN If_block_1 ELSE If_block_1'
    pass


def p_if_block_1(p):
    '''If_block_1 : Data_def
    | If_block'''
    pass


def p_match_block(p):
    '''Match_block : WHEN Expr MATCH Match_block_1'''
    pass


def p_match_block_1(p):
    ' Match_block_1 : VERTICALBAR Pattern COLON Data_def1 Match_block_2 '
    pass


def p_match_block_2(p):
    '''Match_block_2 : VERTICALBAR Pattern COLON Data_def1 Match_block_2
    | empty'''
    pass

#为了避免symbol的Code被覆盖
def p_data_def_1(p):
    'Data_def1 : Data_def'
    pass

def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    print("Simple_equation",p[1].objects)


def p_lhs(p):
    '''Lhs : LPARENTHESE RPARENTHESE
    | Lhs_id Lhs_1'''
    p[0]=lex_value("Lhs")
    if p[1].value!='(':
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)


def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | empty'''
    p[0]=lex_value("Lhs_1")
    if len(p)!=2:
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


# not finish
def p_lhs_id(p):
    '''Lhs_id : LV6ID
              | UNDERLINE'''
    p[0]=p[1]

# not finish
def p_user_op_decl_1(p):
    '''User_op_decl_1 : Size_decl
                      | empty'''
    pass


def p_size_decl(p):
    '''Size_decl : LSHIFT Id_one_or_more_with_comma RSHIFT 
                 | LSHIFT RSHIFT'''
    pass


def p_user_op_decl_2(p):
    '''User_op_decl_2 : Where_decl
                        | empty'''
    pass

def p_where_decl(p):
    '''Where_decl : WHERE Typevar Where_decl_1 Numeric_kind'''
    pass
    

def p_where_decl_1(p):
    '''Where_decl_1 : COMMA Typevar Where_decl_1
                    | empty'''
    pass

def p_typevar(p):
    '''Typevar : SINGLEQUOTE LV6ID'''
    pass

def p_user_op_decl_3(p):
    '''User_op_decl_3 : Spec_decl
                        | empty'''
    #TODO:Spec_decl
    pass

def p_spec_decl(p):
    '''Spec_decl : SPECIALIZE Path_id'''
    pass

def p_in_params(p):
    'In_Params : Params'
    pass


def p_out_params(p):
    'Out_Params : Params'
    pass


def p_params(p):
    'Params : LPARENTHESE Params_1 RPARENTHESE'
    pass

def p_params_1(p):
    '''Params_1 : Var_decls Params_2
    | empty'''
    pass


def p_params_2(p):
    '''Params_2 : SEMICOLON Var_decls Params_2
    | empty'''
    pass


def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
    pass


def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
    pass


def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
    pass


def p_var_id_1(p):
    '''Var_id_1 : CLOCK
    | empty'''
    pass


def p_var_id_2(p):
    '''Var_id_2 : PROBE
    | empty'''
    pass


# not finish
def p_var_decls_2(p):
    '''Var_decls_2 : When_decl
                    | empty'''
    #TODO:when_decl未完成
    pass

def p_when_decl(p):
    '''When_decl : WHEN Clock_expr'''
    #TODO:未完成
    pass

def p_clock_expr(p):
    '''Clock_expr : LV6ID
    | NOT LV6ID
    | LPARENTHESE LV6ID MATCH Pattern RPARENTHESE'''
    #TODO:未完成
    pass

def p_var_decls_3(p):
    '''Var_decls_3 : Default_decl
    | empty'''
    pass


def p_default_decl(p):
    '''Default_decl : DEFAULT EQU Expr'''
    pass


def p_var_decls_4(p):
    '''Var_decls_4 : Last_decl
    | empty'''
    pass


def p_last_decl(p):
    '''Last_decl : LAST EQU Expr'''
    pass


def p_package(p):
    'Package : PACKAGE'
    pass


def p_const_block(p):
    'Const_block : CONST Const_block_1'
    pass


def p_const_block_1(p):
    '''Const_block_1 : Const_decl SEMICOLON Const_block_1
    | empty'''
    pass


def p_const_decl(p):
    '''Const_decl : Interface_status LV6ID COLON Type_expr EQU Expr
    | Interface_status LV6ID COLON Type_expr'''
    pass


def p_interface_status(p):
    '''Interface_status : Visibility_zero_or_one External
    | Visibility_zero_or_one'''
    pass


def p_visibility_zero_or_one(p):
    '''Visibility_zero_or_one : Visibility
    | empty'''
    pass


def p_external(p):
    'External : IMPORTED'
    pass


def p_visibility(p):
    '''Visibility : PRIVATE
    | PUBLIC'''
    pass


def p_sensor_block(p):
    'Sensor_block : SENSOR Sensor_block_1'
    pass


def p_sensor_block_1(p):
    '''Sensor_block_1 : Sensor_decl SEMICOLON Sensor_block_1
    | empty'''
    pass


def p_sensor_decl(p):
    'Sensor_decl : Id_one_or_more_with_comma COLON Type_expr'
    pass


def p_id_one_or_more_with_comma(p):
    'Id_one_or_more_with_comma : LV6ID Id_one_or_more_with_comma_1'
    pass


def p_id_one_or_more_with_comma_1(p):
    '''Id_one_or_more_with_comma_1 : COMMA LV6ID Id_one_or_more_with_comma_1
    | empty'''
    pass


# not finish
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
    | LBPARENTHESE Field_decl Type_expr_1 RBPARENTHESE
    | Type_expr EXPONENT Expr'''
    pass


def p_type_expr_1(p):
    '''Type_expr_1 : COMMA Field_decl Type_expr_1
    | empty'''
    pass


def p_field_decl(p):
    '''Field_decl : LV6ID COLON Type_expr'''
    pass

def p_path_1(p):
    '''Path_1 : DOUBLECOLON LV6ID Path_1
    | empty '''
    p[0]=lex_value("Path_1")
    if len(p)!=2:
        p[0].value=p[1].value+p[2].value+p[3].value
    
def p_path_id(p):
    '''Path_id : LV6ID Path_1'''
    p[0]=lex_value("Path_id")
    p[0].value=p[1].value+p[2].value
    # print("Path_id===",p[0].value)
    
def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    p[0]=lex_value("Id_expr")
    # if len(p)==2:
    #     print("Id_expr",p[1].value)


# not finish
# 若是Arith_expr,则是各个object相加，否则直接赋值
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
    #TODO:Mixed_constructor未完成
    pass


# pre：需要在output中添加一个mem
def p_tempo_expr(p):
    '''Tempo_expr : Expr ARROW Expr
    | PRE Expr
    | FBY LPARENTHESE List SEMICOLON Expr SEMICOLON List RPARENTHESE
    | Expr TIMES Expr
    | Expr WHEN Clock_expr
    | MERGE LPARENTHESE Expr SEMICOLON List Tempo_expr_1 RPARENTHESE'''
    #TODO:times when merge未完成
    p[0]=lex_value("Tempo_expr")

def p_tempo_expr_1(p):
    '''Tempo_expr_1 : SEMICOLON List Tempo_expr_1
                    | empty'''
    pass


def p_relation_expr(p):
    '''Relation_expr : Expr EQU Expr
    | Expr NOEQU Expr
    | Expr LESS Expr
    | Expr GREATER Expr
    | Expr LESSEQU Expr
    | Expr GREATEREQU Expr'''
    # print("Relation_expr")
    pass

# 往符号表添加一个局部变量存储if表达式的结果。if (boolExpr){ localVar=Expr1;}else{ localVar=Expr2;}
def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr
    | LPARENTHESE CASE Expr OF Switch_expr_1 RPARENTHESE'''
    # print("Swith_expr")
    pass

def p_switch_expr_1(p):
    'Switch_expr_1 : Case_expr Switch_expr_2'
    pass


def p_switch_expr_2(p):
    '''Switch_expr_2 : Case_expr Switch_expr_2
    | empty'''
    pass


def p_case_expr(p):
    'Case_expr : VERTICALBAR Pattern COLON Expr'
    pass


def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | Pattern_1 INTEGERNUM
    | Pattern_1 TYPED_INTEGER
    | Bool_atom
    | UNDERLINE'''
    pass


def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
    pass


def p_arith_expr(p):
    '''Arith_expr : LPARENTHESE Expr COLON Type_expr RPARENTHESE'''
    # print("Arith_expr1")
    pass


def p_arith_expr_unary(p):
    '''Arith_expr : MINUS Expr %prec UMINUS
    | PLUS Expr %prec UPLUS
    | LNOT Expr'''
    # print("Arith_expr2")
    pass


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
    # print("Arith_expr3")
    pass

def p_apply_expr(p):
    '''Apply_expr : Operator LPARENTHESE List RPARENTHESE'''
    node=graphTree(p[1].value,"applyFunc")
    global curNode
    curNode.son.append(node)

    
# not finish
def p_prefix(p):
    '''Prefix : Path_id'''
    #TODO:PREFIXOP没有添加，PREFIXOP需要在scade_lex.py里面添加
    p[0]=p[1]
    # print("Prefix==",p[0].value)

# not finish
def p_operator(p):
    '''Operator : Prefix
    | LPARENTHESE Prefix LSHIFT Operator_1 RSHIFT RPARENTHESE
    | LPARENTHESE MAKE Path_id RPARENTHESE
    | LPARENTHESE FLATTEN Path_id RPARENTHESE
    | LPARENTHESE Iterator Operator LSHIFT Expr RSHIFT RPARENTHESE
    | LPARENTHESE ACTIVATE Operator EVERY Clock_expr RPARENTHESE
    | LPARENTHESE ACTIVATE Operator EVERY Expr DEFAULT Expr RPARENTHESE
    | LPARENTHESE ACTIVATE Operator EVERY Expr INITIAL DEFAULT Expr RPARENTHESE
    | LPARENTHESE RESTART EVERY Expr RPARENTHESE
    | LPARENTHESE Iterator_mw Operator LSHIFT Expr RSHIFT IF Expr DEFAULT Expr RPARENTHESE
    | LPARENTHESE FOLDW Operator LSHIFT Expr RSHIFT IF Expr RPARENTHESE
    | LPARENTHESE FOLDWI Operator LSHIFT Expr RSHIFT IF Expr RPARENTHESE'''
    #TODO:
    # print("Operator")
    p[0]=lex_value("Operator")
    if len(p)==2:
        p[0]=p[1]

def p_operator_1(p):
    '''Operator_1 : Expr Operator_2
    | empty'''
    pass

def p_operator_2(p):
    '''Operator_2 : COMMA Expr Operator_2
    | empty'''
    pass

def p_iterator(p):
    '''Iterator : MAP
    | FOLD
    | MAPI
    | FOLDI
    | MAPFOLD
    | MAPFOLD INTEGERNUM
    | MAPFOLDI
    | MAPFOLDI INTEGERNUM'''
    pass

def p_iterator_mw(p):
    '''Iterator_mw : MAPW
    | MAPWI
    | MAPFOLDW
    | MAPFOLDW INTEGERNUM
    | MAPFOLDWI
    | MAPFOLDWI INTEGERNUM'''
    pass


def p_list_expr(p):
    '''List_expr : LPARENTHESE List RPARENTHESE'''
    # print("List_expr")
    pass


def p_list(p):
    '''List : List_1
    | empty'''
    pass


def p_list_1(p):
    '''List_1 : Expr List_2'''
    pass

def p_list_2(p):
    '''List_2 : COMMA Expr List_2
    | empty'''
    pass


# typed_integer和typed_float未添加
def p_atom(p):
    '''Atom : Bool_atom
    | INTEGERNUM
    | FLOATNUM
    | CHARACTER
    | TYPED_INTEGER
    | TYPED_FLOAT'''
    pass


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    pass


def p_bool_expr(p):
    '''Bool_expr : NOT Expr
    | HASHTAG LPARENTHESE List RPARENTHESE'''
    # print("Bool_expr1")
    pass


def p_bool_expr_bin(p):
    '''Bool_expr : Expr AND Expr
    | Expr OR Expr
    | Expr XOR Expr'''
    # print("Bool_expr2")
    pass


def p_struct_expr(p):
    '''Struct_expr : Expr POINT LV6ID
    | LBPARENTHESE Label_expr Struct_expr_1 RBPARENTHESE'''
    # print("Struct_expr")
    pass


def p_struct_expr_1(p):
    '''Struct_expr_1 : COMMA Label_expr Struct_expr_1
    | empty'''
    pass


def p_label_expr(p):
    '''Label_expr : LV6ID COLON Expr'''
    pass

def p_array_expr(p):
    '''Array_expr : LBRACKET List RBRACKET
    | Expr Index'''
    # print("Array_expr1")
    pass

def p_array_expr2(p):
    '''Array_expr : REVERSE Expr
    | Expr AT Expr'''
    # print("Array_expr2")
    pass

def p_array_expr3(p):
    '''Array_expr : Expr EXPONENT Expr
    | Expr LBRACKET Expr TPOINT Expr RBRACKET'''
    # print("Array_expr3")
    pass

def p_array_expr4(p):
    '''Array_expr : LPARENTHESE Expr POINT Array_expr_1 DEFAULT Expr RPARENTHESE
    | TRANSPOSE LPARENTHESE Expr SEMICOLON INTEGERNUM SEMICOLON INTEGERNUM RPARENTHESE'''
    # print("Array_expr4")
    pass

def p_array_expr_1(p):
    '''Array_expr_1 : Label_or_index Array_expr_2'''
    pass

def p_array_expr_2(p):
    '''Array_expr_2 : Label_or_index Array_expr_2
    | empty'''
    pass

def p_label_or_index(p):
    '''Label_or_index : POINT LV6ID
    | Index'''
    pass

def p_index(p):
    '''Index : LBRACKET Expr RBRACKET'''
    pass

def p_mixed_constructor(p):
    '''Mixed_constructor : LPARENTHESE Expr WITH Mixed_constructor_1 EQU Expr RPARENTHESE'''
    #TODO:未完成
    # print("Mixed_constructor")
    pass

def p_mixed_constructor_1(p):
    '''Mixed_constructor_1 : Label_or_index Mixed_constructor_2'''
    pass

def p_mixed_constructor_2(p):
    '''Mixed_constructor_2 : Label_or_index Mixed_constructor_2
    | empty'''
    pass

def p_error(p):
    print("Syntax error in input!")


def p_empty(p):
    'empty :'
    p[0] = lex_value('Empty')

def get_parse(strs):
    global program
    parser = yacc(debug=1)
    pattern1 = r'#pragma [a-zA-Z0-9_!"$#%&\'()*+,\-./:;_<=>?@\\^`|{}~\s]*?#end'
    strs=re.sub(pattern1, '', strs, flags=re.MULTILINE)
    
    pattern2 = r'\#[\w]+'
    strs = re.sub(pattern2, '', strs)
    
    pattern3 = re.compile(r'/\*.*?\*/',re.DOTALL)
    strs = re.sub(pattern3,'',strs)
    
    print("=======strs=====\n", strs)
    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)
    writeFile(programNode)
    # return program, GlobalEnv

if __name__ == '__main__':
    parser = yacc(debug=1)
    file = open("airBrakeSystem.txt",'r')
    strs = file.read()
    get_parse(strs)
    parser.parse(strs, lexer=scade_lexer)


#package airdynamic有问题