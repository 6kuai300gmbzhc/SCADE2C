from ply.yacc import yacc
from scade_lex import scade_lex,get_tokens,tokens,lex_value
from SymbolClass import *

isPackage=0
packageName=""
op_kind_id=""
intArr=["int8","int16","int32","int64","uint8","uint16","uint32","uint64"]
floatArr=["float32","float64"]
typeArr=['bool','int8','int16','int64','int32','uint8','uint16','uint32','uint64','float32','float64','char','enum','array']

scade_lexer=scade_lex()
GlobalEnv=SymbolTable('Global')
thisEnv=GlobalEnv
program=None

def generate_head_file():
    op_kind_symbol=thisEnv.getSymbol(op_kind_id)
    name=op_kind_symbol.Name
    head_content=""
    head_content+="_"+name+"_H_\n"+"#define _"+name+"_H_\n"
    head_content+="#include \"kcg_types.h\"\n\n"
    head_content+="typedef struct {\n"
    #input_params
    # print(len(op_kind_symbol.Params))
    for input_name in op_kind_symbol.Params:
        symbol=thisEnv.getSymbol(input_name)
        head_content+=type_change(symbol.Type)+" "+input_name+";\n"
    head_content+="} inC_"+name+";\n"

    #out_params
    head_content += "\n\ntypedef struct {\n"
    for output_name in op_kind_symbol.Returns:
        symbol=thisEnv.getSymbol(output_name)
        head_content += type_change(symbol.Type) + " " + output_name + ";"+"\n"
    head_content += "} outC_" + name + ";\n"

    #function
    head_content+="\nextern void "+name+"(inC_"+name+" *inC, outC_"+name+" *outC);\n"
    head_content+="\nextern void "+name+"_reset(outC_"+name+" *outC);\n"
    head_content += "\nextern void " + name + "_init(outC_" + name + " *outC);\n"
    filename="./output/"+name+".h"
    # print("head_content")
    print(head_content)
    with open(filename,'w') as f:
        f.write(head_content)

def generate_c_file(body):
    op_kind_symbol = thisEnv.getSymbol(op_kind_id)
    c_content = "#include \"kcg_consts.h\"\n#include \"kcg_sensors.h\"\n"
    name = op_kind_symbol.Name
    c_content += "#include \"%s.h\"\n" % name
    c_content += "void %s(inC_%s *inC, outC_%s *outC)\n{\n" % (name,name,name)
    c_content += body
    c_content += "\n}\n"

    c_content += "void %s_init(outC_%s *outC)\n{\n" % (name,name)
    for para in op_kind_symbol.Returns:
        symbol = thisEnv.getSymbol(para)
        if symbol.IsArray==False:
            c_content += "outC->%s=%s;\n" % (para,getParamsInitValue(thisEnv.getSymbol(para).Type))
    for elem in op_kind_symbol.fbyList:
        c_content += "for(int idx=0;idx<%s;idx++){\n%s[idx]=%s;\n}\n"%(objectsToString(thisEnv.getSymbol(elem.fbyIdx).Code),thisEnv.getSymbol(elem.fbyArr).changeName(),getParamsInitValue(thisEnv.getSymbol(elem.fbyArr).Type))
    c_content += "}\n"

    c_content += "void %s_reset(outC_%s *outC)\n{\n" % (name,name)
    for para in thisEnv.SymbolTable.values():
        if para.Kind=="Pre":
            c_content += "outC->%s=%s;\n"%(para.Name,getParamsInitValue(thisEnv.getSymbol(para.Name).Type))
    c_content += "}\n"
    filename = "./output/%s.c" %(name)
    print(c_content)
    with open(filename,'w') as f:
        f.write(c_content)

def getName(initStr):
    symbol=thisEnv.getSymbol(op_kind_id)
    for i in range(100):
        target=initStr
        if i!=0:
            target+=str(i)
        # if target in symbol.Params or target in symbol.Returns or target in symbol.StaticParams:
        #     continue
        # else:
        #     return target
        if target in thisEnv.SymbolTable:
            continue
        else:
            return target
    return initStr
def getParamsInitValue(type):
    if type in intArr:
        return "kcg_lit_%s(0)" % type
    elif type in floatArr:
        return "kcg_lit_%s(0.0)" % type
    elif type=="bool":
        return "kcg_true"
    else:
        typeSymbol=thisEnv.getSymbol(type)
        if typeSymbol!=None:
            return getParamsInitValue(typeSymbol.Type)

def type_initial(type,value):
    content=""
    if type=="bool":
        content+="kcg_"+value
    else:
        content+="kcg_lit_"+type+"("+str(value)+")"
    return content


def objectsToString(objects,num=0):
    # type=""
    sstr=""
    for elem in objects:
        if elem.strs=='lv6id':
            symbol=thisEnv.getSymbol(elem.value)
            # type=symbol.Type
            sstr+=symbol.changeName()
        elif elem.strs=='integernum':
            sstr += "kcg_lit_%s(%s)" % (elem.type,str(elem.value))
        elif elem.strs=='lnot_lv6id':
            sstr += "kcg_lnot_%s" % elem.type
        elif elem.strs=='true':
            sstr+="kcg_true"
        elif elem.strs=='false':
            sstr+="kcg_false"
        # elif elem.strs=='Pre':
        #     symbol=thisEnv.getSymbol(elem.value)
        #     symbol.Type=type
        #     sstr+=symbol.changeName()
        else:
            sstr+=elem.value
    return sstr
def getTypefromObjects(objects):
    type=""
    for objs in objects:
        for elem in objs:
            if elem.strs=='lv6id':
                symbol=thisEnv.getSymbol(elem.value)
                type=symbol.Type
                break
    return type

def setObjectsType(objects,type):
    for elem in objects:
        symbol=thisEnv.getSymbol(elem.value)
        if symbol==None:
            if elem.type=='':
                elem.type=type
        else:
            if symbol.Type=='':
                symbol.Type=type

def exprToNum(objects):
    #逆波兰表达式得到值
    num=0
    for elem in objects:
        if elem.strs=='lv6id':
            symbol=thisEnv.getSymbol(elem.value)
            print("symbol.Code=",symbol.Code)
        print("exprToNum:",elem.strs,elem.value)
    return num



def getArrSize(objects):
    str=""
    print("getArrSize",objects)
    for elem in reversed(objects):
        if len(elem) == 1:
            if elem[0].strs == 'integernum':
                str += "[%s]" % elem[0].value
        else:
            str += "["
            for subElem in elem:
                str += subElem.value
            str += "]"
    return str

def defToString(defList):
    content=""
    for elem in defList:
        content+=objectsToString(elem)
    return content

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
    | Type_block
    | Sensor_block
    | Package_decl
    | User_op_decl'''
    # p[0]=p[1]
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
    external=True
    public=True
    if len(p[1].objects)==1:
        external=False
    if p[1].objects[0].value=="private":
        public=False
    typeSymbol=Symbol(p[2].value,"Type",public,external)
    thisEnv.setSymbol(p[2].value,typeSymbol)
    if p[3].strs=='Type_expr':
        typeSymbol.Type=p[3].value
        print("p[3].objects",p[3].objects)
        if len(p[3].objects)!=0:
           typeSymbol.Type='array'
        typeSymbol.Code.extend(p[3].objects)
    elif p[3].strs=='Enum':
        typeSymbol.Type="enum"
        typeSymbol.Code.extend(p[3].objects)


def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    if len(p)==3:
        p[0]=p[2]
def p_type_decl_2(p):
    '''Type_decl_2 : IS Numeric_kind
                   | empty'''
    pass

def p_type_def(p):
    '''Type_def : Type_expr
                | ENUM LBPARENTHESE Id_one_or_more_with_comma RBPARENTHESE'''
    if len(p)==2:
        p[0]=p[1]
    else:
        p[0]=p[3]
        p[0].strs='Enum'
def p_numeric_kind(p):
    '''Numeric_kind : NUMERIC
    | FLOAT
    | INTEGER
    | SIGNED
    | UNSIGNED'''
    pass

#将LV6ID写成Lv6id是为了提前知道包的名字
def p_package_decl(p):
    'Package_decl : Package Visibility_zero_or_one Pack_Lv6id Decls_zero_or_mode END SEMICOLON'
    pass

#每一个function和node都会产生一个对应其函数名的.h和.c文件
def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    # print(p[3].value)
    global thisEnv
    symbol=thisEnv.getSymbol(p[3].value)
    for idx in p[5].objects:
        # print(idx.strs,idx.value)
        symbol.Params.append(idx.value)
    for idx in p[7].objects:
        symbol.Returns.append(idx.value)
    generate_head_file()
    generate_c_file(p[10].value)

    thisEnv=thisEnv.PrevTable


def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0]=p[1]

def p_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
    global thisEnv
    symbol=Symbol(p[1].value,'OpKind')
    thisEnv.setSymbol(p[1].value,symbol)
    global op_kind_id
    op_kind_id=p[1].value

    newEnv=SymbolTable(p[1].value,thisEnv)
    thisEnv.ChildTableList.append(newEnv)
    thisEnv=newEnv

def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0]=p[1]

# def equationToString(objects):
#     sstr = ""
#     sstr+=objectsToString(objects)
#     sstr+=";\n"
#     op_kind_symbol = thisEnv.getSymbol(op_kind_id)
#     if op_kind_symbol.IsInit == True:
#         sstr += "outC->" + op_kind_symbol.InitName + "=kcg_false;\n"
#     for elem in thisEnv.SymbolTable.values():
#         if elem.Kind == "Pre":
#             sstr += "OutC->" + elem.Name + "="
#             sstr += objectsToString(elem.Code) + ";\n"
#     return sstr

def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL'''
    p[0]=lex_value("Opt_body")
    op_kind_symbol=thisEnv.getSymbol(op_kind_id)
    if len(p)==2:
        pass
    else:
        if len(p)==6 or len(p)==7:
            for elem in p[2].objects:
                symbol=thisEnv.getSymbol(elem.value)
                p[0].value+="kcg_%s %s;\n"%(symbol.Type,symbol.Name)
        for elem in thisEnv.SymbolTable.values():#在程序中使用到的临时变量
            if elem.Kind=="TmpVar":
                p[0].value+="kcg_%s %s;\n"%(elem.Type,elem.Name)
        if len(p)==3:
            p[0].value+=defToString(p[1].beforeObjects)
            p[0].value+=defToString(p[1].objects)
            p[0].value+=defToString(p[1].afterObjects)
        else:
            p[0].value+=defToString(p[4].beforeObjects)
            p[0].value+=defToString(p[4].objects)
            p[0].value+=defToString(p[4].afterObjects)
        if op_kind_symbol.InitName!="":
            initSymbol=thisEnv.getSymbol(op_kind_symbol.InitName)
            p[0].value+="if(%s){%s=kcg_false;}"%(initSymbol.changeName(),initSymbol.changeName())


def p_signal_block_zero_or_one(p):
    '''Signal_block_zero_or_one : empty'''
    pass

def p_local_block_zero_or_one(p):
    '''Local_block_zero_or_one : Local_block
    | empty'''
    p[0]=p[1]

def p_local_block(p):
    '''Local_block : VAR Local_block_1'''
    p[0]=p[2]

def p_local_block_1(p):
    '''Local_block_1 : Var_decls SEMICOLON Local_block_1
    | empty'''
    p[0]=lex_value("Local_block_1")
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[3].objects)


def p_equation_zero_or_more_with_semicolon(p):
    '''Equation_zero_or_more_with_semicolon : Equation SEMICOLON Equation_zero_or_more_with_semicolon
    | empty'''
    p[0]=lex_value("Equation_zero_or_more_with_semicolon")
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].afterObjects.extend(p[1].afterObjects)
        p[0].objects.extend(p[3].objects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[3].afterObjects)

def p_equation(p):
    '''Equation : Simple_equation'''
    p[0]=lex_value("Equation")
    p[0].objects.extend(p[1].objects)
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].afterObjects.extend(p[1].afterObjects)

def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    #若出现input1=1->pre(2)。2作为mem_pre加进符号表，此时的类型未知，初始化会出现错误。因此需要找到lhs的类型
    #先去Expr找是否存在类型为Pre的符号
    p[0]=lex_value('Simple_equation')
    op_kind_symbol = thisEnv.getSymbol(op_kind_id)
    type=getTypefromObjects(p[1].objects)

#objects [["expr"]]
#beforeObjects[["lhs",“lhs=expr”]]
    for elem in p[3].objects:
        setObjectsType(elem,type)
    for elem in p[3].beforeObjects:
        print(elem[1])
        setObjectsType(elem,type)
    for elem in p[3].afterObjects:
        setObjectsType(elem,type)

    for idx in range(len(p[1].objects)):
        defList=list()
        defList.extend(p[1].objects[idx])
        defList.append(p[2])
        defList.extend(p[3].objects[idx])
        defList.append(lex_value("",";\n"))
        p[0].objects.append(defList)

    p[0].beforeObjects.extend(p[3].beforeObjects)
    p[0].afterObjects.extend(p[3].afterObjects)




def p_lhs(p):
    '''Lhs : LPARENTHESE RPARENTHESE
    | Lhs_id Lhs_1'''
    p[0]=lex_value("Lhs")
    if p[1].strs!='lparenthese':
        p[0].objects.append([p[1]])
        p[0].objects.extend(p[2].objects)



def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | empty'''
    p[0]=lex_value("Lhs_1")
    if len(p)==4:
        p[0].objects.append([p[2]])
        p[0].objects.extend(p[3].objects)


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
        p[0].objects.extend(p[3].objects)

def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
#直接将var_decls_2 var_decls_3 var_decls_4设置为空
    p[0]=lex_value('Var_decls')
    symbol=thisEnv.getSymbol(p[1].value)
    symbol.Type=p[4].value
    symbol.Code.extend(p[4].objects)
    for i in range(len(p[2].objects)):
        symbol=thisEnv.getSymbol(p[2].objects[i].value)
        symbol.Type=p[4].value
        symbol.Code.extend(p[4].value)
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
    p[0]=lex_value("var_decls_1")
    if len(p)==4:
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)

def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
    p[0]=p[3]
    # print("Var_id",p[3].value)
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
        type=p[4].value
        symbol.arrSize.extend(p[4].objects)
        setObjectsType(p[6].objects[0],type)
        symbol.Code=p[6].objects[0]
        thisEnv.setSymbol(p[2].value,symbol)
    elif len(p)==5:
        symbol=Symbol(p[2].value,'Const',p[4].value,public,external,isPackage,packageName)
        symbol.arrSize.extend(p[4].objects)
        thisEnv.setSymbol(p[2].value,symbol)


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
        symbol.Code.extend(p[3].objects);


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
        p[0].objects.extend(p[3].objects)


#not finish
def p_type_expr(p):
    '''Type_expr : BOOL Type_expr_2
    | SIGNED LSHIFT INTEGERNUM RSHIFT Type_expr_2
    | INT8 Type_expr_2
    | INT16 Type_expr_2
    | INT32 Type_expr_2
    | INT64 Type_expr_2
    | UNSIGNED LSHIFT INTEGERNUM RSHIFT Type_expr_2
    | UINT8 Type_expr_2
    | UINT16 Type_expr_2
    | UINT32 Type_expr_2
    | UINT64 Type_expr_2
    | FLOAT32 Type_expr_2
    | FLOAT64 Type_expr_2
    | CHAR Type_expr_2
    | Path_id Type_expr_2'''
    p[0]=lex_value('Type_expr')
    if len(p)==3:
        p[0].value=p[1].value
        if len(p[2].objects)!=0:
            p[0].objects.extend(p[2].objects)
    else:
        #没写完，需要将INTCONST改为Expr
        #需要计算出Expr表达式代表的值，Expr可能是静态数组，结构体。
        # num=exprToNum(p[3].objects)
        if p[1].strs=='signed':
            type="int"+str(p[3].value)
        elif p[1].strs=='unsigned':
            type="uint"+str(p[3].value)
        p[0].value=type
        pass

def p_type_expr_2(p):
    '''Type_expr_2 : EXPONENT Expr Type_expr_2
    | empty'''
    p[0]=lex_value("Type_expr_2")
    if len(p)==4:
        p[0].objects.append(p[2].objects[0])
        p[0].objects.extend(p[3].objects)
def p_path_1(p):
    '''Path_1 : DOUBLECOLON LV6ID Path_1
    | empty '''
    if len(p)!=2:
        p[0]=lex_value("Path_1")
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    else:
        p[0]=p[1]

def p_path_id(p):
    '''Path_id : LV6ID Path_1'''
    if len(p[2].objects)!=0:
        elem=p[2].objects[-1]
        symbol=Symbol(elem.value,"PathId")
        symbol.Kind="PathId"
        symbol.Code.append(p[1])
        symbol.Code.extend(p[2].objects[:-1])
        thisEnv.setSymbol(elem.value, symbol)
        p[0]=lex_value("lv6id",elem.value)
    else:
        p[0]=p[1]


def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    symbol=thisEnv.getSymbol(op_kind_id)
    p[0]=lex_value("Id_expr")
    if len(p)==2:
        p[0].objects.append(p[1])
    elif len(p)==4:
        lastName = getName("mem_last")
        symbol.Returns.append(lastName)
        lastSymbol = Symbol(lastName, "Last", "")
        lastSymbol.IsReturn = True
        thisEnv.setSymbol(lastName, lastSymbol)
        p[0].objects.append(lex_value("lv6id", lastName))
        afterList=list()
        afterList.extend([lex_value("lv6id",lastName),lex_value("=","=")])
        afterList.append(p[3])
        afterList.append(lex_value("",";\n"))
        p[0].afterList.append(afterList)
    elif len(p)==3:
        pass




#not finish
#若是Arith_expr,则是各个object相加，否则直接赋值
def p_expr(p):
    '''Expr : Id_expr
    | Atom
    | Tempo_expr
    | Arith_expr
    | Relation_expr
    | List_expr
    | Switch_expr
    | Bool_expr'''
    p[0]=lex_value("Expr")
    if p[1].strs!='List_expr' and p[1].strs!='Tempo_expr' and p[1].strs!='Switch_expr':
        p[0].objects=[p[1].objects]
    else:
        p[0].objects=p[1].objects
    p[0].beforeObjects=p[1].beforeObjects
    p[0].afterObjects=p[1].afterObjects

#arrow对应于C语言的三目运算符
#pre：需要在output中添加一个mem
def p_tempo_expr(p):
    '''Tempo_expr : Expr ARROW Expr
    | PRE Expr
    | FBY LPARENTHESE List SEMICOLON Expr SEMICOLON List RPARENTHESE'''
    #若是init操作符，则需要向out结构体中添加init。若有重名，则使用init1（依此递增）
    symbol = thisEnv.getSymbol(op_kind_id)
    p[0] = lex_value("Tempo_expr")
    if len(p)==4 and p[2].value=='->':
        if symbol.InitName=="":
            initName=getName("init")
            symbol.InitName=initName
            initSymbol=Symbol(initName,"Init","bool")
            initSymbol.IsReturn=True
            thisEnv.setSymbol(initName,initSymbol)
            symbol.Returns.append(initName)
        # p[0].objects.append(lex_value('lv6id',initName,'bool'))
        # p[0].objects.append(lex_value("?","?","str"))
        if len(p[1].objects)!=len(p[3].objects):
            print("tempo_expr arrow:error")
            exit()

        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)

        for idx in range(len(p[1].objects)):
            initName = symbol.InitName
            initElem = getName("initElem")
            initLex = lex_value("initElem", initElem)
            thisEnv.setSymbol(initElem, Symbol(initElem, "TmpVar"))
            befDefList = list()
            befDefList.extend([lex_value("if(", "if(", "str"), lex_value("lv6id", initName), lex_value("){\n", "){\n")])
            befDefList.extend([lex_value("lv6id", initElem), lex_value("=", "=")])
            befDefList.extend(p[1].objects[idx])
            befDefList.append(lex_value("", ";\n}else{\n"))
            befDefList.extend([lex_value("lv6id", initElem), lex_value("=", "=")])
            befDefList.extend(p[3].objects[idx])
            befDefList.append(lex_value(";\n}\n", ";\n}\n"))
            p[0].beforeObjects.append(befDefList)

            p[0].objects.append([initLex])

        p[0].afterObjects.extend(p[1].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
        # for elem in p[0].beforeObjects:
        #     print("elem=",elem)
    elif len(p)==3:
        #若是pre操作符，需要向out添加mem_pre，用来存储上一个周期的值。若在符号表未找到，则无需添加mem_pre。
        #则此时只需要输出上一个周期的值。可能出现pre(2)
        #expr可能是列表
        for idx in range(len(p[2].objects)):
            preName = getName("mem_pre")
            symbol.Returns.append(preName)
            preSymbol = Symbol(preName, "Pre", "")
            preSymbol.IsReturn = True
            thisEnv.setSymbol(preName, preSymbol)

            p[0].objects.append([lex_value("lv6id", preName, "")])
            afterDefList = list()
            afterDefList.extend([lex_value("lv6id", preName), lex_value("=", "=")])
            afterDefList.extend(p[2].objects[idx])
            afterDefList.append(lex_value("", ";\n"))
            p[0].afterObjects.extend(p[2].afterObjects)
            p[0].afterObjects.append( afterDefList)

        p[0].beforeObjects.extend(p[2].beforeObjects)
    elif len(p)==9:
        #若是fby操作符，首先在outC结构体中添加一个idx和数组
        #fby(input1;cycle;input2) cycle必须是静态表达式
        if symbol.InitName=="":
            initName=getName("init")
            symbol.InitName=initName
            symbol.IsInit=True
            initSymbol=Symbol(initName,"Init","bool")
            initSymbol.IsReturn=True
            thisEnv.setSymbol(initName,initSymbol)
            symbol.Returns.append(initName)
        if len(p[3].objects)!=len(p[7].objects):
            print("tempo_expr fby:error")
            exit()

        p[0].beforeObjects += p[3].beforeObjects + p[5].beforeObjects + p[7].beforeObjects
        p[0].afterObjects += p[3].afterObjects + p[5].afterObjects + p[7].afterObjects
        for idx in range(len(p[3].objects)):
            fbyIdx = getName("fbyIdx")
            fbyArr = getName("fbyArray")

            type = getTypefromObjects(p[5].objects)
            if type == "":
                type = "int32"
            fbyIdxSymbol = Symbol(fbyIdx, "FbyIdx", type)
            fbyIdxSymbol.IsReturn = True
            fbyArrSymbol = Symbol(fbyArr, "FbyArr")
            fbyArrSymbol.IsReturn = True
            fbyArrSymbol.IsArray = True
            thisEnv.setSymbol(fbyIdx, fbyIdxSymbol)
            thisEnv.setSymbol(fbyArr, fbyArrSymbol)
            fbyIdxSymbol.Code.extend(p[5].objects)
            setObjectsType(fbyIdxSymbol.Code, type)
            symbol.Returns.append(fbyIdx)
            symbol.Returns.append(fbyArr)
            symbol.fbyList.append(fbyClass(fbyIdx, fbyArr))

            p[0].objects.append(
                [lex_value("lv6id", fbyArr, ""), lex_value("[", "[", "str"), lex_value("lv6id", fbyIdx, "int32"),
                 lex_value("]", "]", "str")])

            befDefList = list()

            befDefList.extend([lex_value("", "if("), lex_value("lv6id", thisEnv.getSymbol(op_kind_id).InitName),
                               lex_value(")\n{", ")\n{")])
            befDefList.append(lex_value("", "for(int idx=0;idx<%s;idx++){\n" % objectsToString(p[5].objects[idx])))
            befDefList.extend(
                [lex_value("lv6id", fbyArr), lex_value("", "["), lex_value("lv6id", fbyIdx), lex_value("", "]=")])
            # 注意是List，先考虑list为1
            for elem in p[7].objects[idx]:
                befDefList.extend(elem)
            # befDefList.extend(p[7].objects)
            befDefList.append(lex_value("", ";\n}\n}"))
            p[0].beforeObjects.append(befDefList)


            aftDefList = list()
            aftDefList.extend(
                [lex_value("lv6id", fbyArr), lex_value("", "["), lex_value("lv6id", fbyIdx), lex_value("", "]=")])
            for elem in p[3].objects[idx]:
                aftDefList.extend(elem)
            aftDefList.append(lex_value("", ";\n"))
            aftDefList.extend(
                [lex_value("lv6id", fbyIdx), lex_value("", "=("), lex_value("lv6id", fbyIdx), lex_value("", "+1)%(")])
            aftDefList.extend(p[5].objects[idx])
            aftDefList.append(lex_value("", ");\n"))
            p[0].afterObjects.append( aftDefList)

        # for elem in p[0].beforeObjects:
        #     print("fby",elem)

def p_relation_expr(p):
    '''Relation_expr : Expr Bin_relation_op Expr'''
    p[0]=lex_value("Relation_expr")
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].beforeObjects.extend(p[3].beforeObjects)

    if len(p[1].objects)!=len(p[3].objects) and len(p[1].objects)!=1:
        print("relation_epxr:error")
        exit(0)
    p[0].objects.extend(p[1].objects[0])
    p[0].objects.extend(p[2])
    p[0].objects.extend(p[3].objects[0])

    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].afterObjects.extend(p[3].afterObjects)

def p_bin_relation_op(p):
    '''Bin_relation_op : EQU
    | NOEQU
    | LESS
    | GREATER
    | LESSEQU
    | GREATEREQU'''
    p[0]=p[1]
    if p[1].strs=='NOEQU':
        p[1].value='!='
    elif p[1].strs=='EQU':
        p[1].value='=='


def judgeIsEnum(objects):
    print()
    for elem in objects:
        if elem.strs=='lv6id':
            symbol=thisEnv.getSymbol(elem.value)
            if symbol!=None:
                value=symbol.Type
                while value not in typeArr:
                    symbol=thisEnv.getSymbol(value)
                    value=symbol.Type
                if value=='enum':
                    return symbol.Name
    return ""


def checkEnum(eName,objects):
    isUnderline=False
    sum=0
    eSymbol=thisEnv.getSymbol(eName)
    eDict=dict()
    for elem in eSymbol.Code:
        eDict[elem.value]=1
    for elem in objects:
        if elem[0][0].strs=='_':
            isUnderline=True
        elif elem[0][0].strs=='lv6id':
            eDict[elem[0][0].value]-=1
    for key,value in eDict:
        if value==1:
            sum+=1
    if (sum>=1 and isUnderline==True) or (sum==0 and isUnderline==False):
        return True

#往符号表添加一个局部变量存储if表达式的结果。if (boolExpr){ localVar=Expr1;}else{ localVar=Expr2;}
def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr
    | LPARENTHESE CASE Expr OF Switch_expr_1 RPARENTHESE'''
    p[0] = lex_value("Switch_expr")
    if p[1].value=='if':
        if len(p[4].objects)!=len(p[6].objects):
            print("switch_expr if error")
            exit(0)
        p[0].beforeObjects += p[2].beforeObjects + p[4].beforeObjects + p[6].beforeObjects
        for idx in range(len(p[4].objects)):
            ifTmp = getName("ifTmp")
            ifSymbol = Symbol(ifTmp, "TmpVar")
            thisEnv.setSymbol(ifTmp, ifSymbol)
            befDefList=list()
            befDefList.append(lex_value("", "if("))
            befDefList.extend(p[2].objects[0])
            befDefList.extend([lex_value("", "){\n"), lex_value("lv6id", ifTmp), lex_value("", "=")])
            befDefList.extend(p[4].objects[idx])
            befDefList.append(lex_value("", ";\n}else{\n"))
            befDefList.append(lex_value("lv6id", ifTmp))
            befDefList.append(lex_value("", "="))
            befDefList.extend(p[6].objects[idx])
            befDefList.append(lex_value("", ";\n}\n"))
            p[0].beforeObjects.append(befDefList)

            p[0].objects.append([lex_value("lv6id", ifTmp)])


        p[0].afterObjects += p[2].afterObjects + p[4].afterObjects + p[6].afterObjects
    else:
        # 如果是char，integernum需要添加default。如果是path_id，则是枚举
        print(p[5].objects)
        exprSymbol=thisEnv.getSymbol(p[2].value)
        eName=judgeIsEnum(p[3].objects[0])
        if eName!='':
            if checkEnum(eName,p[5].objects[0])==False:
                print("Case error")
            else:
                pass
        else:
            pass

def p_switch_expr_1(p):
    'Switch_expr_1 : Case_expr Switch_expr_2'
    p[0]=lex_value('Switch_expr_1')
    for idx in range(len(p[1].objects)):
        p[0].objects.append([p[1].objects[idx]])
    for idx in range(len(p[2].objects)):
        p[0].objects[idx].extend(p[2].objects[idx])
    print("Switch_expr_1", p[0].objects)
def p_switch_expr_2(p):
    '''Switch_expr_2 : Case_expr Switch_expr_2
    | empty'''
    p[0]=lex_value("Switch_expr_2")
    if len(p)==3:
        for idx in range(len(p[1].objects)):
            p[0].objects.append([p[1].objects[idx]])
        for idx in range(len(p[2].objects)):
            p[0].objects[idx].extend(p[2].objects[idx])
        print("Switch_expr_2",p[0].objects)

def p_case_expr(p):
    'Case_expr : VERTICALBAR Pattern COLON Expr'
    p[0]=lex_value('Case_expr')
    for idx in range(len(p[4].objects)):
        tmpList=list()
        tmpList.append([p[2]])
        tmpList.append(p[4].objects[idx])
        p[0].objects.append(tmpList)

def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | Pattern_1 INTEGERNUM
    | Bool_atom
    | UNDERLINE'''
    print(p[1].strs,p[1].value)
    if len(p)==3:
        p[0]=p[2]
        p[2].value=str(-p[2].value)
    else:
        p[0]=p[1]

def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
    p[0]=p[1]

def p_arith_expr(p):
    '''Arith_expr : Unary_arith_op Expr
    | Expr Bin_arith_op Expr'''
    p[0]=lex_value("Arith_expr")
    if len(p)==4:
        p[0].objects.extend(p[1].objects[0])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects[0])
        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[1].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
    elif len(p)==3:
        p[0].beforeObjects.extend(p[2].beforeObjects)
        if p[1].strs=='-':
            p[0].objects.extend(p[1])
        elif p[1].strs=='lnot':
            #新增一个变量，将其strs设置为lnot_lv6id。当遍历到这个变量时，将其转化为kcg_lnot_type
            p[0].objects.extend([lex_value("lnot_lv6id"),lex_value("(","(")])
            p[0].objects.extend(p[2].objects[0])
            p[0].objects.append(lex_value(")",")"))
        p[0].afterObjects.extend(p[2].afterObjects)


def p_list_expr(p):
    '''List_expr : LPARENTHESE List RPARENTHESE'''
    p[0]=lex_value("List_expr")
    p[0].objects.extend(p[2].objects)
    p[0].beforeObjects.extend(p[2].beforeObjects)
    p[0].afterObjects.extend(p[2].afterObjects)

def p_list(p):
    '''List : List_1
    | empty'''
    p[0] = lex_value("List")
    if p[1].strs=="List_1":
        p[0].objects.extend(p[1].objects)
        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].afterObjects.extend(p[1].afterObjects)

def p_list_1(p):
    '''List_1 : Expr List_2'''
    p[0]=lex_value("List_1")
    p[0].objects.extend(p[1].objects)
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].objects.extend(p[2].objects)
    p[0].beforeObjects.extend(p[2].beforeObjects)
    p[0].afterObjects.extend(p[2].afterObjects)

def p_list_2(p):
    '''List_2 : COMMA Expr List_2
    | empty'''
    p[0]=lex_value("List_2")
    if len(p)==4:
        p[0].objects.extend(p[2].objects)
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].objects.extend(p[3].objects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[3].afterObjects)


def p_unary_arith_op(p):
    '''Unary_arith_op : MINUS
    | PLUS
    | LNOT'''
    p[0]=p[1]

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
    #当操作符是除了+-*/以外的，需要转化成C对应的操作符
    if p[1].strs=='MOD':
        p[0].value=' % '
    elif p[1].strs==' LAND ':
        p[0].value='&'
    elif p[1].strs=='LOR':
        p[0].value=' | '
    elif p[1].strs=='LXOR':
        p[0].value=' ^ '
    elif p[1].strs=='LSL':
        p[0].value=' << '
    elif p[1].strs=='LSR':
        p[0].value=' >> '

#not finish
def p_atom(p):
    '''Atom : Bool_atom
    | INTEGERNUM
    | FLOATNUM
    | CHARACTER'''
    p[0]=lex_value("Atom")
    p[0].objects.append(p[1])


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    p[0]=p[1]


def p_bool_expr(p):
    '''Bool_expr : NOT Expr
    | Expr Bin_bool_op Expr
    | HASHTAG LPARENTHESE List RPARENTHESE'''
    p[0]=lex_value("Bool_expr")
    if len(p)==3:
        p[1].value='!'
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects[0])
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
    elif len(p)==4:
        p[0].objects+=p[1].objects[0]
        p[0].objects.append(p[2])
        p[0].objects+=p[3].objects[0]
        p[0].beforeObjects+=p[1].beforeObjects+p[3].beforeObjects
        p[0].afterObjects+=p[1].afterObjects+p[3].afterObjects
    elif len(p)==5:
        for idx in range(len(p[3].objects)):
            p[0].objects.append(lex_value("","("))
            p[0].objects.extend(p[3].objects[idx])
            p[0].objects.append(lex_value("", ")"))
            if idx!=len(p[3].objects)-1:
                p[0].objects.append(lex_value("","+"))
        p[0].objects.append(lex_value("","<=1"))

def p_bin_bool_op(p):
    '''Bin_bool_op : AND
    | OR
    | XOR'''
    if p[1].strs=='and':
        p[1].value=' & '
    elif p[1].strs=='or':
        p[1].value=' | '
    elif p[1].strs=='xor':
        p[1].value=' ^ '
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
    str=type
    if type in list:
        str="kcg_"+type
    return str

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
    strs = str("sensor Sensor1:int32;\
    sensor Sensor2:int32;")
    string_tokens=get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes=parser.parse(strs,lexer=scade_lexer)
    # print(nodes)


