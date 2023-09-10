from ply.yacc import yacc
from scade_lex import scade_lex,get_tokens,tokens,lex_value
from SymbolClass import *

isPackage=0
packageName=""
operator_flag=""

scade_lexer=scade_lex()
GlobalEnv=SymbolTable('Global')
thisEnv=GlobalEnv
program=None

def symbol_change_name(symbol):
    name=""
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
    print(len(op_kind_symbol.Params))
    for input_name in op_kind_symbol.Params:
        symbol=thisEnv.getSymbol(input_name)
        head_content+="kcg_"+symbol.Type+" "+input_name+";"
    head_content+="\n} inC_"+name+";\n"
    #out_params
    head_content += "\n\ntypedef struct {\n"
    # input_params
    print(len(op_kind_symbol.Returns))
    for output_name in op_kind_symbol.Returns:
        symbol=thisEnv.getSymbol(output_name)
        head_content += "kcg_" + symbol.Type + " " + output_name + ";"
    head_content += "\n} outC_" + name + ";\n"
    #function
    head_content+="\n\nextern void "+name+"(inC_"+name+" *inC, outC_"+name+" *outC);\n"
    head_content+="\n\nextern void "+name+"_reset(outC_"+name+" *outC);\n"
    head_content += "\n\nextern void " + name + "_init(outC_" + name + " *outC);\n"
    filename="./output/"+name+".h"
    with open(filename,'w') as f:
        f.write(head_content)

def generate_c_file(symbol,body):
    c_content="#include\"kcg_consts.h\"\n"+"#include\"kcg_sensors.h\"\n"
    name=symbol.Name
    c_content+="#include \""+name+".h\"\n"
    c_content+="void "+name+"(inC_"+name+" *inC, "+"outC_"+name+" *outC)\n{\n"
    c_content+=body
    c_content+="\n}\n"

    c_content += "void " + name + "_init("+"outC_" + name + " *outC)\n{\n"
    c_content += "}\n"

    c_content += "void " + name + "_reset(" + "outC_" + name + " *outC)\n{\n"
    c_content += "}\n"
    filename="./output/"+name+".c"
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
    print(p[3].value)
    symbol=thisEnv.getSymbol(p[3].value)
    for idx in p[5].objects:
        print(idx.strs,idx.value)
        symbol.Params.append(idx.value)
    for idx in p[7].objects:
        symbol.Returns.append(idx.value)
    generate_head_file(symbol)
    generate_c_file(symbol,p[10].value)

def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0]=p[1]

def p_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
    symbol=Symbol(p[1].value,'Package')
    thisEnv.setSymbol(p[1].value,symbol)

def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0]=p[1]

def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON'''
    p[0]=lex_value("Opt_body")
    if len(p)==2:
        p[0].value=p[1].value
    elif len(p)==3:
        p[0].value=p[1].value+p[2].value
    print(p[0].value)

def p_equation(p):
    '''Equation : Simple_equation'''
    p[0]=lex_value("Equation")
    p[0].value+=p[1].value

def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    p[0]=lex_value('Simple_equation')
    # for i in p[3].objects:
    #     print(i.strs,i.value)
    # print("Lhs")
    # for j in p[1].objects:
    #     print(j.strs)
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
    '''User_op_decl_1 : empty'''
    pass

def p_user_op_decl_2(p):
    '''User_op_decl_2 : empty'''
    pass

def p_user_op_decl_3(p):
    '''User_op_decl_3 : empty'''
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
    '''Const_block : CONST Const_decl SEMICOLON Const_block
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
        symbol.Value=p[6].value
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
def p_expr(p):
    '''Expr : Id_expr
    | Atom
    | Arith_expr'''
    # p[0]=lex_value("Expr")
    # if p[1].strs=="Id_expr" or p[1].strs=='Arith_expr':
    #     p[0].objects.extend(p[1].objects)
    # else:
    #     p[0].objects.append(p[1])
    p[0]=p[1]

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

def p_error(p):
    print("Syntax error in input!")

def p_empty(p):
    'empty : '
    p[0]=lex_value('Empty')

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

if __name__=='__main__':
    parser=yacc(debug=1)
    # strs=str("package NoPackage\
    #  const e:bool=true;\
    #  const d:int32=0;\
    #  const imported c:int32;\
    #  const private imported f:int8;\
    #  end;")
    strs=str("function plus_two (x:int8) returns (y:int8) y=x+2;")
    string_tokens=get_tokens(strs)
    # print(string_tokens)
    scade_lexer.set_tokens(string_tokens)
    nodes=parser.parse(strs,lexer=scade_lexer)
    # print(nodes)


