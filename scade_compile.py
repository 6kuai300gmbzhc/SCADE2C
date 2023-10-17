from ply.yacc import yacc
from scade_lex import scade_lex,get_tokens,tokens,lex_value
from SymbolClass import *

isPackage=0
packageName=""
op_kind_id=""
intArr=["int8","int16","int32","int64","uint8","uint16","uint32","uint64"]
floatArr=["float32","float64"]

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
        print(symbol.Name,symbol.Kind,symbol.Type)
        head_content+="kcg_"+symbol.Type+" "+input_name+";\n"
    head_content+="} inC_"+name+";\n"

    #out_params
    head_content += "\n\ntypedef struct {\n"
    for output_name in op_kind_symbol.Returns:
        symbol=thisEnv.getSymbol(output_name)
        print(symbol.Name, symbol.Kind, symbol.Type)
        head_content += "kcg_" + symbol.Type + " " + output_name + ";"+"\n"
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
    c_content="#include \"kcg_consts.h\"\n#include \"kcg_sensors.h\"\n"
    name=op_kind_symbol.Name
    c_content+="#include \"%s.h\"\n" % name
    c_content+="void %s(inC_%s *inC, outC_%s *outC)\n{\n" % (name,name,name)
    c_content+=body
    c_content+="\n}\n"

    c_content += "void %s_init(outC_%s *outC)\n{\n" % (name,name)
    for para in op_kind_symbol.Returns:
        symbol=thisEnv.getSymbol(para)
        if symbol.IsArray==False:
            c_content+="outC->%s=%s;\n" % (para,getParamsInitValue(thisEnv.getSymbol(para)))
    for elem in op_kind_symbol.fbyList:
        c_content+="for(int idx=0;idx<%s;idx++){\n%s[idx]=%s;\n}\n"%(objectsToString(thisEnv.getSymbol(elem.Idx).Code),thisEnv.getSymbol(elem.Array).changeName(),getParamsInitValue(thisEnv.getSymbol(elem.Array)))
    c_content += "}\n"

    c_content += "void %s_reset(outC_%s *outC)\n{\n" % (name,name)
    for para in thisEnv.SymbolTable.values():
        if para.Kind=="Pre":
            c_content += "outC->%s=%s;\n"%(para.Name,getParamsInitValue(thisEnv.getSymbol(para.Name)))
    c_content += "}\n"
    filename="./output/%s.c" %(name)
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
def getPreName():
    symbol=thisEnv.getSymbol(op_kind_id)
    preName="mem_pre"
    idx=0
    if idx!=0:
        preName+=str(idx)
    while preName in symbol.Returns:
        preName="mem_"+preName
    return preName
def getParamsInitValue(symbol):
    if symbol.Type in intArr:
        return "kcg_lit_%s(0)" % symbol.Type
    elif symbol.Type in floatArr:
        return "kcg_lit_%s(0.0)" % symbol.Type
    elif symbol.Type=="bool":
        return "kcg_true"
def type_initial(type,value):
    print("type_initial ",type,value)
    content=""
    if type=="bool":
        content+="kcg_"+value
    else:
        content+="kcg_lit_"+type+"("+str(value)+")"
    return content


def objectsToString(objects,num=0):
    # type=""
    sstr=""
    # print("objectsToString")
    op_kind_symbol=thisEnv.getSymbol(op_kind_id)
    for elem in objects:
        # print(elem.strs,elem.value)
        if elem.strs=='lv6id':
            symbol=thisEnv.getSymbol(elem.value)
            # type=symbol.Type
            sstr+=symbol.changeName()
        elif elem.strs=='intconst':
            sstr+="kcg_lit_%s(%s)" % (elem.type,str(elem.value))
        # elif elem.strs=='Pre':
        #     symbol=thisEnv.getSymbol(elem.value)
        #     symbol.Type=type
        #     sstr+=symbol.changeName()
        else:
            sstr+=elem.value
    return sstr
def getTypefromObjects(objects):
    type=""
    for obj in objects:
        # print(obj.strs,obj.value)
        if obj.strs=='lv6id':
            symbol=thisEnv.getSymbol(obj.value)
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
        if len(p)==3:
            p[0].value+=p[1].value
        else:
            p[0].value+=p[4].value
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
    for elem in p[2].objects:
        print(elem.value)

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
        p[0].value=p[1].value+p[3].value

def p_equation(p):
    '''Equation : Simple_equation'''
    p[0]=p[1]

def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    #若出现input1=1->pre(2)。2作为mem_pre加进符号表，此时的类型未知，初始化会出现错误。因此需要找到lhs的类型
    #先去Expr找是否存在类型为Pre的符号
    p[0]=lex_value('Simple_equation')
    op_kind_symbol = thisEnv.getSymbol(op_kind_id)
    type=getTypefromObjects(p[1].objects)

    # print("type=",type)
    print("setObjectsType3")
    setObjectsType(p[1].objects,type)
    setObjectsType(p[3].objects,type)
    setObjectsType(p[1].initObjects,type)
    setObjectsType(p[3].initObjects,type)

    p[0].value=objectsToString(p[3].initObjects);
    #查找是否存在->符号。 一个node最后只写一个if(out->Init){处理fby和init内容}
    p[0].value+="%s %s %s;"%(objectsToString(p[1].objects),p[2].value,objectsToString(p[3].objects))

    p[0].value+=objectsToString(p[3].afterObjects)





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
    print("p_var_decls", symbol.Name, symbol.Type)
    for i in range(len(p[2].objects)):
        symbol=thisEnv.getSymbol(p[2].objects[i].value)
        symbol.Type=p[4].value
        print("p_var_decls",symbol.Name, symbol.Type)
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
        symbol.Value=objectsToString(p[6].objects)
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
    | INT8
    | INT16
    | INT32
    | INT64
    | UINT8
    | UINT16
    | UINT32
    | UINT64
    | FLOAT32
    | FLOAT64
    | CHAR'''
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
    | Arith_expr
    | List_expr
    | Switch_expr'''
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
    | PRE Expr
    | FBY LPARENTHESE List SEMICOLON Expr SEMICOLON List RPARENTHESE'''
    #若是init操作符，则需要向out结构体中添加init。若有重名，则使用init1（依此递增）
    symbol = thisEnv.getSymbol(op_kind_id)
    initName=""
    p[0] = lex_value("Tempo_expr")
    if len(p)==4:
        if symbol.InitName=="":
            initName=getName("init")
            symbol.InitName=initName
            initSymbol=Symbol(initName,"Init","bool")
            initSymbol.IsReturn=True
            thisEnv.setSymbol(initName,initSymbol)
            symbol.Returns.append(initName)
        # p[0].objects.append(lex_value('lv6id',initName,'bool'))
        # p[0].objects.append(lex_value("?","?","str"))
        initElem=getName("initElem")
        initLex=lex_value("initElem",initElem)
        thisEnv.setSymbol(initElem,Symbol(initElem,"LocalVar"))
        p[0].initObjects.extend(p[1].initObjects)
        p[0].initObjects.extend(p[3].initObjects)
        p[0].initObjects.extend([lex_value("if(","if(","str"),lex_value("lv6id",initName),lex_value("){\n","){\n")])
        p[0].initObjects.extend([lex_value("lv6id",initElem),lex_value("=","=")])
        p[0].initObjects.extend(p[1].objects)
        p[0].initObjects.append(lex_value("",";\n}else{\n"))
        p[0].initObjects.extend([lex_value("lv6id",initElem),lex_value("=","=")])
        p[0].initObjects.extend(p[3].objects)
        p[0].initObjects.append(lex_value(";\n}",";\n}"))
        p[0].objects.append(initLex)
        p[0].afterObjects.extend(p[1].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
    elif len(p)==3:
        #若是pre操作符，需要向out添加mem_pre，用来存储上一个周期的值。若在符号表未找到，则无需添加mem_pre
        #则此时只需要输出上一个周期的值。可能出现pre(2)
        #向symbolTable添加一个字典，保存pre对应的值，还有fby对应的值
        preName=getPreName()
        symbol.Returns.append(preName)
        preSymbol=Symbol(preName,"Pre","")
        preSymbol.IsReturn=True
        thisEnv.setSymbol(preName,preSymbol)
        p[0].initObjects.extend(p[2].initObjects)
        p[0].objects.append(lex_value("lv6id",preName,""))
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].afterObjects.extend([lex_value("lv6id",preName),lex_value("=","=")])
        p[0].afterObjects.extend(p[2].objects)
        p[0].afterObjects.append(lex_value("",";\n"))
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
        fbyIdx=getName("fbyIdx")
        fbyArr=getName("fbyArray")

        type=getTypefromObjects(p[5].objects)
        if type=="":
            type="int32"
        fbyIdxSymbol=Symbol(fbyIdx,"FbyIdx",type)
        fbyIdxSymbol.IsReturn=True
        fbyArrSymbol=Symbol(fbyArr,"FbyArr")
        fbyArrSymbol.IsReturn=True
        fbyArrSymbol.IsArray=True
        thisEnv.setSymbol(fbyIdx,fbyIdxSymbol)
        thisEnv.setSymbol(fbyArr,fbyArrSymbol)
        fbyIdxSymbol.Code.extend(p[5].objects)
        setObjectsType(fbyIdxSymbol.Code,type)
        symbol.Returns.append(fbyIdx)
        symbol.Returns.append(fbyArr)

        p[0].objects.append(lex_value("lv6id",fbyArr,""))
        p[0].objects.append(lex_value("[","[","str"))
        p[0].objects.append(lex_value("lv6id",fbyIdx,"int32"))
        p[0].objects.append(lex_value("]","]","str"))
        p[0].initObjects.extend([p[3].initObjects,p[5].initObjects,p[7].initObjects])
        p[0].initObjects.extend([lex_value("","if("),lex_value("lv6id",thisEnv.getSymbol(op_kind_id).InitName),lex_value(")\n{",")\n{")])
        p[0].initObjects.extend([lex_value("lv6id",fbyArr),lex_value("","["),lex_value("lv6id",fbyIdx),lex_value("","]=")])
        p[0].initObjects.extend(p[7].objects)
        p[0].initObjects.append(lex_value("",";\n}\n}"))
        p[0].afterObjects+=p[3].afterObjects+p[5].afterObjects+p[7].afterObjects
        p[0].afterObjects.extend([lex_value("lv6id",fbyArr),lex_value("","["),lex_value("lv6id",fbyIdx),lex_value("","]=")])
        p[0].afterObjects.extend(p[3].objects)
        p[0].afterObjects.extend([lex_value("lv6id",fbyIdx),lex_value("","=("),lex_value("lv6id",fbyIdx),lex_value("","+1)%(")])
        p[0].afterObjects.extend(p[5].objects)
        p[0].afterObjects.extend(lex_value("",");\n"))






#往符号表添加一个局部变量存储if表达式的结果。if (boolExpr){ localVar=Expr1;}else{ localVar=Expr2;}
def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr'''

    pass


def p_arith_expr(p):
    '''Arith_expr : Expr Bin_arith_op Expr'''
    p[0]=lex_value("Arith_expr")
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].initObjects.extend(p[1].initObjects)
        p[0].initObjects.extend(p[3].initObjects)
        p[0].afterObjects.extend(p[1].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)

def p_list_expr(p):
    '''List_expr : LPARENTHESE List RPARENTHESE'''
    p[0]=lex_value("List_expr")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].initObjects.extend(p[2].initObjects)
    p[0].afterObjects.extend(p[2].afterObjects)
def p_list(p):
    '''List : List_1
    | empty'''
    p[0] = lex_value("List")
    if p[1].strs=="List_1":
        p[0].objects.extend(p[1].objects)
        p[0].initObjects.extend(p[1].initObjects)
        p[0].afterObjects.extend(p[1].afterObjects)

def p_list_1(p):
    '''List_1 : Expr List_2'''
    p[0]=lex_value("List_1")
    if p[2].strs=="Empty":
        p[0].objects.extend(p[1].objects)
        p[0].initObjects.extend(p[1].initObjects)
        p[0].afterObjects.extend(p[1].afterObjects)

def p_list_2(p):
    '''List_2 : COMMA Expr List_2
    | empty'''
    if len(p)==2:
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


