from ply.yacc import yacc
from scade_lex import scade_lex,get_tokens,tokens,lex_value
from SymbolClass import *

isPackage=0
# global isStatemachine
isStatemachine=0
packageName=""
operator_flag=""

scade_lexer=scade_lex()
GlobalEnv=SymbolTable('Global')
thisEnv=GlobalEnv
program=None

def symbol_change_name(symbol):
    name=symbol.Name
    if symbol.IsInput is True:
        name="inC->"+symbol.Name
    elif symbol.IsReturn is True:
        name="outC->"+symbol.Name
    return name

def generate_head_file(op_kind_symbol):
    name=op_kind_symbol.Name
    head_content=""
    head_content+="_"+name+"_H_\n"+"#define _"+name+"_H_\n"
    head_content+="#include \"kcg_types.h\"\n\n"
    head_content+="typedef struct {\n"
    #input_params
    # print(len(op_kind_symbol.Params))
    for input_name in op_kind_symbol.Params:
        symbol=thisEnv.getSymbol(input_name)
        head_content+="kcg_"+symbol.Type+" "+input_name+";"
    head_content+="\n} inC_"+name+";\n"
    #out_params
    head_content += "\n\ntypedef struct {\n"
    # input_params
    # print(len(op_kind_symbol.Returns))
    for output_name in op_kind_symbol.Returns:
        symbol=thisEnv.getSymbol(output_name)
        head_content += "kcg_" + symbol.Type + " " + output_name + ";"
    if isStatemachine==1:
        head_content+="\nSSM_ST state_nxt;\n"
    head_content += "\n} outC_" + name + ";\n"
    #function
    head_content+="\n\nextern void "+name+"(inC_"+name+" *inC, outC_"+name+" *outC);\n"
    head_content+="\n\nextern void "+name+"_reset(outC_"+name+" *outC);\n"
    head_content += "\n\nextern void " + name + "_init(outC_" + name + " *outC);\n"
    filename="./output/"+name+".h"
    with open(filename,'w') as f:
        f.write(head_content)

def generate_c_file(symbol,body,init_body='',reset_body=''):
    c_content="#include\"kcg_consts.h\"\n"+"#include\"kcg_sensors.h\"\n"
    name=symbol.Name
    c_content+="#include \""+name+".h\"\n"
    c_content+="void "+name+"(inC_"+name+" *inC, "+"outC_"+name+" *outC)\n{\n"
    c_content+=body
    c_content+="\n}\n"

    c_content += "void " + name + "_init("+"outC_" + name + " *outC)\n{\n"
    c_content += init_body
    c_content += "}\n"

    c_content += "void " + name + "_reset(" + "outC_" + name + " *outC)\n{\n"
    c_content += reset_body
    c_content += "}\n"
    filename="./output/"+name+".c"
    print(c_content)
    with open(filename,'w') as f:
        f.write(c_content)


def p_program(p):
    'Program : Decls_zero_or_mode'
    # p[0]=p[1]
    pass

#not finish
def p_decls_zero_or_mode(p):
    '''Decls_zero_or_mode : Decls Decls_zero_or_mode
    | empty'''
    # p[0]=p[1]+p[2]
    pass

#not finish
def p_decls(p):
    '''Decls : Const_block
    | Sensor_block
    | Package_decl
    | User_op_decl'''
    # p[0]=p[1]
    pass

#将LV6ID写成Lv6id是为了提前知道包的名字
def p_package_decl(p):
    'Package_decl : Package Visibility_zero_or_one Pack_Lv6id Decls_zero_or_mode END SEMICOLON'
    pass

#每一个function和node都会产生一个对应其函数名的.h和.c文件
def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    # print(p[3].value)
    symbol=thisEnv.getSymbol(p[3].value)
    if isStatemachine==1:
        symbol.isStatemachine==True # 该node name为状态机名字
        print('状态机', p[3].value, '的状态列表: ', symbol.StateList)
        print('TODO: 即将构建reset, init函数body传给generate_c_file')
    for idx in p[5].objects:
        # print(idx.strs,idx.value)
        symbol.Params.append(idx.value)
    for idx in p[7].objects:
        symbol.Returns.append(idx.value)
    generate_head_file(symbol)
    generate_c_file(symbol,p[10].value)  # TODO: 加入 init, reset 函数 body

def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0]=p[1]

def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
    symbol=Symbol(p[1].value,'Package')
    thisEnv.setSymbol(p[1].value,symbol)

def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    p[0]=p[1]
    symbol=Symbol(p[1].value,'State')
    thisEnv.setSymbol(p[1].value,symbol)


def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0]=p[1]
    if p[1].strs=='node':
        symbol=Symbol('init','Var','bool')
        thisEnv.setSymbol('init',symbol)



def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON'''
    p[0]=lex_value("Opt_body")
    if len(p)==2:
        p[0].value=p[1].value
    elif len(p)==3:
        # p[0].value=p[1].value+p[2].value
        p[0].value=p[1].value # Simple_equation生成过程自带分号无需再加, 如果是控制块, 花括号后不应当出现分号

def p_equation(p):
    '''Equation : Simple_equation
                | Control_block Return'''
    p[0]=lex_value("Equation")
    if len(p) == 2:
        print("Equation\n",p[0].value, ' end of p[0].value')
        print("Equation\n",p[1].value, ' end of p[1].value')
        p[0].value+=p[1].value
    elif len(p)==3:
        p[0].value+=p[1].value+p[2].value


def p_control_block(p):
    '''Control_block : State_machine'''
    p[0]=lex_value("Control_block")
    p[0].value+=p[1].value

def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0]=lex_value("Return")
    # node以及function定义的时候已经写了return的参数列表，C代码使用 outC->var_name = 为返回值赋值，所以这里的return语句不需要再生成
    pass

def p_returns_var(p):
    '''Returns_var : LV6ID'''
    # 目前设计 仅返回单个变量, 不能返回空变量, 这个生成式没用
    p[0]=p[1]

def p_state_machine(p):
    '''State_machine : AUTOMATON State_machine_1'''
    # 原来应当为 Id_zero_or_one 省略状态机名字为空的情况，默认没有ID
    p[0]=lex_value("State_machine")
    # switch (state_sel)
    p[0].value+="SSM_ST state_sel = outC->state_nxt;\n"
    p[0].value+="switch (state_sel)\n{\n"
    for statement in p[2].objects: # 每个状态已经在生成式中构造好了数据流和状态转移语句
        p[0].value+=statement.value+"\n"
    p[0].value+="}\n"
    

def p_state_machine_1(p):
    '''State_machine_1 : State_decl State_machine_1
                       | empty'''
    p[0]=lex_value("State_machine_1")
    if len(p) == 3:
        p[0].objects.append(p[1]) # 拼接多个状态定义
        p[0].objects.extend(p[2].objects)
        print('状态定义', p[1].value)
    
def p_state_decl(p):
    '''State_decl ::= State_decl_1 State_decl_2 STATE State_Lv6id State_decl_3 Data_def State_decl_4'''
    # TODO: 目前仅实现弱迁移，state_decl_3 的 unless语句强迁移未实现
    p[0]=lex_value("State_decl")
    
    # p[4] 为状态名，p[6]为状态内部赋值语句equation, p[7]为 transition
    p[0].value+='case '+p[4].value+':\n'
    p[0].value+=p[6].value+'\n'
    p[0].value+=p[7].value+'\n'

def p_state_decl_1(p):
    '''State_decl_1 : INITIAL
                    | empty'''
    print("State_decl_1: ", p[1])
    # TODO: Do something in nodename.c init, reset function
    pass

def p_state_decl_2(p):
    '''State_decl_2 : FINAL
                    | empty'''
    pass

def p_state_decl_3(p):
    '''State_decl_3 : empty'''
    pass

def p_data_def(p):
    '''Data_def : Simple_equation SEMICOLON
                | empty'''
    # 在状态机中仅实现了简单的无 LET...TEL语句
    p[0]=lex_value("Data_def")
    if len(p)==3:
        p[0].value+=p[1].value+p[2].value

def p_state_decl_4(p):
    '''State_decl_4 : UNTIL Transition SEMICOLON'''
    p[0]=lex_value("State_decl_4")
    p[0].value+=p[2].value

def p_transition(p):
    '''Transition : IF LV6ID Target'''
    # 省略 Scade 语法中原有的 Arrow, 因为ARROW是一个token运算符, 暂未实现 p_arrow
    # If Expr 的 表达式简化成一个 LV6ID
    print("Transition: ", p[1], p[2], p[3])
    p[0]=lex_value("Transition")
    p[0].value+="if("+p[2].value+")"
    p[0].value+="{\n  "+p[3].value+"\n}\n"
    p[0].value+='break;'

def p_target(p):
    '''Target : RESTART LV6ID'''
    # 目前仅实现 restart 关键字，状态重新开始，resume暂缓实现
    print("Target: ", p[1], p[2])
    # outC->state_nxt = state_name;
    p[0]=lex_value("Target")
    p[0].value+="outC->state_nxt = "+p[2].value+";"

    # 自底向上分析，在最底层设置全局变量, 当前node为状态机
    print('自底向上分析，在最底层设置全局变量, 当前node为状态机')
    global isStatemachine
    isStatemachine=1
    
def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    p[0]=lex_value('Simple_equation')
    type=""
    for lex in p[1].objects:
        if lex.strs=='lv6id':
            symbol=thisEnv.getSymbol(lex.value)
            type=symbol.Type
            p[0].value+=symbol_change_name(symbol)
    p[0].value+=" "+p[2].value+" "
    for lex in p[3].objects:
        if lex.strs=='lv6id':
            symbol=thisEnv.getSymbol(lex.value)
            p[0].value+=symbol_change_name(symbol)
        elif lex.strs=='intconst':
            p[0].value+="kcg_lit_"+type+"("+str(lex.value)+")"
        else:
            p[0].value+=" "+lex.value+" "

def p_lhs(p):
    '''Lhs : LPARENTHESE RPARENTHESE
    | Lhs_id Lhs_1'''
    p[0]=lex_value("Lhs")
    if p[1].strs!='lparenthese':
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)



def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | empty'''
    p[0]=lex_value("Lhs_1")
    if len(p)==4:
        p[0].objects.append(p[2])


#not finish
def p_lhs_id(p):
    '''Lhs_id : LV6ID'''
    p[0]=p[1]

#not finish
def p_user_op_decl_1(p):
    '''User_op_decl_1 : Size_decl
                      | empty'''
    p[0]=p[1]
    pass

def p_size_decl(p):
    '''Size_decl : LSHIFT Id_one_or_more_with_comma RSHIFT 
                 | LSHIFT RSHIFT'''
    p[0]=lex_value('Size_decl')

def p_user_op_decl_2(p):
    '''User_op_decl_2 : empty'''
    p[0]=p[1]
    pass

def p_user_op_decl_3(p):
    '''User_op_decl_3 : empty'''
    p[0]=p[1]
    pass

def p_in_params(p):
    'In_Params : Params'
    p[0]=p[1]
    for var in p[0].objects:
        symbol=thisEnv.getSymbol(var.value)
        symbol.IsInput=True

def p_out_params(p):
    'Out_Params : Params'
    p[0]=p[1]
    for var in p[0].objects:
        symbol=thisEnv.getSymbol(var.value)
        symbol.IsReturn=True

def p_params(p):
    'Params : LPARENTHESE Params_1 RPARENTHESE'
    p[0]=p[2]

def p_params_1(p):
    '''Params_1 : Var_decls Params_2
    | empty'''
    p[0]=lex_value('params_1')
    p[0].objects.extend(p[1].objects)
    if len(p)==3:
        p[0].objects.extend(p[2].objects)

def p_params_2(p):
    '''Params_2 : SEMICOLON Var_decls Params_2
    | empty'''
    p[0]=lex_value('params_2')
    if len(p)==4:
        p[0].objects.extend(p[2].objects)

def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
#直接将var_decls_2 var_decls_3 var_decls_4设置为空
    p[0]=lex_value('Var_decls')
    symbol=thisEnv.getSymbol(p[1].value)
    symbol.Type=p[4].value
    for i in range(len(p[2].objects)):
        symbol=thisEnv.getSymbol(p[2].objects[i].value)
        symbol.Type=p[4].value
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
    p[0]=lex_value("var_decls_1")
    if len(p)==4:
        p[0].objects.append(p[2])

def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
    p[0]=p[3]
    symbol=Symbol(p[3].value,'Var','')
    thisEnv.setSymbol(p[3].value,symbol)


def p_var_id_1(p):
    '''Var_id_1 : CLOCK
    | empty'''
    p[0]=p[1]

def p_var_id_2(p):
    '''Var_id_2 : PROBE
    | empty'''
    p[0]=p[1]

#not finish
def p_var_decls_2(p):
    'Var_decls_2 : empty'

def p_var_decls_3(p):
    'Var_decls_3 : empty'

def p_var_decls_4(p):
    'Var_decls_4 : empty'

def p_package(p):
    'Package : PACKAGE'
    global isPackage
    isPackage=1
    p[0]=p[1]

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
    #Interface_status表示该变量是private or public 。是否是external
    external=True
    public=True
    if len(p[1].objects)==1:
        external=False
    if p[1].objects[0].value=="private":
        public=False
    if len(p)==7:
        symbol=Symbol(p[2].value,'Const',p[4].value,public,external,isPackage,packageName)
        symbol.Value=("".join(map(lambda item:str(item.value),p[6].objects)))
        thisEnv.setSymbol(p[2].value,symbol)
    elif len(p)==5:
        symbol=Symbol(p[2].value,'Const',p[4].value,public,external,isPackage,packageName)
        thisEnv.setSymbol(p[2].value,symbol)
    pass


def p_interface_status(p):
    '''Interface_status : Visibility_zero_or_one External
    | Visibility_zero_or_one'''
    p[0]=lex_value('Interface_status')
    if len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
    elif len(p)==2:
        p[0].objects.append(p[1])
    pass

def p_visibility_zero_or_one(p):
    '''Visibility_zero_or_one : Visibility
    | empty'''
    p[0]=p[1]

def p_external(p):
    'External : IMPORTED'
    # p[0]=lex_value('External')
    p[0]=p[1]

def p_visibility(p):
    '''Visibility : PRIVATE
    | PUBLIC'''
    p[0]=p[1]

def p_sensor_block(p):
    'Sensor_block : SENSOR Sensor_block_1'
    pass

def p_sensor_block_1(p):
    '''Sensor_block_1 : Sensor_decl SEMICOLON Sensor_block_1
    | empty'''
    pass

def p_sensor_decl(p):
    'Sensor_decl : Id_one_or_more_with_comma COLON Type_expr'
    for item in p[1].objects:
        symbol=Symbol(item.value,'Sensor')
        symbol.Type=p[3].value
        thisEnv.setSymbol(item.value,symbol)


def p_id_one_or_more_with_comma(p):
    'Id_one_or_more_with_comma : LV6ID Id_one_or_more_with_comma_1'
    p[0]=lex_value('Id_one_or_more_with_comma')
    p[0].objects.append(p[1])
    if len(p)==3:
        p[0].objects.extend(p[2].objects)


def p_id_one_or_more_with_comma_1(p):
    '''Id_one_or_more_with_comma_1 : COMMA LV6ID Id_one_or_more_with_comma_1
    | empty'''
    p[0]=lex_value('Id_one_or_more_with_comma_1')
    if len(p)==4:
        p[0].objects.append(p[2])


#not finish
def p_type_expr(p):
    '''Type_expr : BOOL
    | INT32
    | INT8'''
    p[0]=lex_value('Type_expr')
    p[0].value=p[1].value

def p_path_id(p):
    'Path_id : LV6ID'
    p[0]=p[1]

def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    p[0]=lex_value("Id_expr")
    if len(p)==2:
        p[0].objects.append(p[1])

#not finish
#若是Arith_expr,则是各个object相加，否则直接赋值
def p_expr(p):
    '''Expr : Id_expr
    | Atom
    | Tempo_expr
    | Arith_expr'''
    # p[0]=lex_value("Expr")
    # if p[1].strs=="Id_expr" or p[1].strs=='Arith_expr':
    #     p[0].objects.extend(p[1].objects)
    # else:
    #     p[0].objects.append(p[1])
    p[0]=p[1]

#arrow对应于C语言的三目运算符
#pre：需要在output中添加一个mem
def p_tempo_expr(p):
    '''Tempo_expr : Expr ARROW Expr
    | PRE Expr'''
    if len(p)==4:
        p[0]=lex_value("Tempo_expr")
        p[0].objects.append(lex_value("(out->init)","(out->init)","str"))
        p[0].objects.append(lex_value("?","?","str"))
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(lex_value(":",":","str"))
        p[0].objects.extend(p[3].objects)
    elif len(p)==3:
        pass




def p_arith_expr(p):
    '''Arith_expr : Expr Bin_arith_op Expr'''
    p[0]=lex_value("Arith_expr")
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


def p_bin_arith_op(p):
    '''Bin_arith_op : PLUS
    | MINUS
    | STAR
    | DIVIDE
    | MOD
    | LAND
    | LOR
    | LXOR
    | LSL
    | LSR'''
    p[0]=p[1]

#not finish
def p_atom(p):
    '''Atom : Bool_atom
    | INTCONST'''
    p[0]=lex_value("Atom")
    p[0].objects.append(p[1])


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    p[0]=p[1]

# def p_error(p):
#     print("Syntax error in input!")

def p_empty(p):
    'empty :'
    pass
    # p[0]=lex_value('Empty')

def get_parse(strs):
    global program
    parser=yacc(debug=1)
    parse=yacc(debug=1)
    string_tokens=get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes=parser.parse(strs,lexer=scade_lexer)
    return program,GlobalEnv

def type_change(type):
    list=["char","bool","float32","float64","size","uint64","uint32","uint16","uint8","int64","int32","int16","int8"]
    if type in list:
        str="kcg_"+type
    return str

def type_initial(type,value):
    print("type_initial ",type,value)
    content=""
    if type=="bool":
        content+="kcg_"+value
    else:
        content+="kcg_lit_"+type+"("+str(value)+")"
    return content

if __name__=='__main__':
    parser=yacc(debug=1)
    #define e kcg_true  define d(kcg_lit_int32(0)) extern const kcg_int32 c
    #extern const kcg_int8 f;
    # strs = str("package NoPackage\
    #         const e:bool=true;\
    #         const d:int32=0;\
    #         const imported c:int32;\
    #         const private imported f:int8;\
    #         end;")
    # strs=str("function plus_two (x:int8) returns (y:int8) y=x+2;")
    # strs = str("sensor Sensor1:int32;\
    # sensor Sensor2:int32;")
    strs = """
    node simple_automaton (i: int32; c: bool) returns (o: int32)
    automaton
        initial state ADD1
            o = i + 1 ;
        until if c restart MINUS1;

        state MINUS1
            o = i - 1;
        until if c restart ADD1;
    returns o;  
    """
    string_tokens=get_tokens(strs)
    # print(string_tokens)
    scade_lexer.set_tokens(string_tokens)
    nodes=parser.parse(strs,lexer=scade_lexer)
    print(nodes)


