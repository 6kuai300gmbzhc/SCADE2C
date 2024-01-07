from ply.yacc import yacc
from scade_lex import scade_lex,get_tokens,tokens,lex_value
from SymbolClass import *
import re
isPackage=0
# global isStatemachine
isStatemachine=0
packageName=""
op_kind_id=""
intArr=["int8","int16","int32","int64","uint8","uint16","uint32","uint64"]
floatArr=["float32","float64"]
typeArr=['bool','int8','int16','int64','int32','uint8','uint16','uint32','uint64','float32','float64','char','enum','array','struct']

scade_lexer=scade_lex()
GlobalEnv=SymbolTable('Global')
thisEnv=GlobalEnv
program=None

def type_change(type):
    list=["char","bool","float32","float64","size","uint64","uint32","uint16","uint8","int64","int32","int16","int8"]
    str=type
    if type in list:
        str="kcg_"+type
    return str
def generate_head_file():
    op_kind_symbol=thisEnv.getSymbol(op_kind_id)
    name=op_kind_symbol.Name
    head_content=""
    head_content+="#ifndef _"+name+"_H_\n"+"#define _"+name+"_H_\n"
    head_content+="#include \"kcg_types.h\"\n\n"
    head_content+="typedef struct {\n"
    #input_params
    # print(len(op_kind_symbol.Params))
    for input_name in op_kind_symbol.Params:
        symbol=thisEnv.getSymbol(input_name)
        print('正在生成head file, 当前op_kind_symbol的input_name:', input_name, '当前作用域: ', thisEnv.EnvName) # TODO: delete debug info
        head_content+="%s %s%s;\n"%(type_change(symbol.Type),input_name,getArrSize(symbol.arrSize))
    head_content+="} inC_"+name+";\n"

    #out_params
    head_content += "\n\ntypedef struct {\n"
    for output_name in op_kind_symbol.Returns:
        symbol=thisEnv.getSymbol(output_name)
        if symbol.Kind=='FbyIdx' or symbol.Kind=='FbyArr':
            continue
        else:
            head_content += type_change(symbol.Type) + " " + output_name + ";"+"\n"
    for fbyElem in op_kind_symbol.fbyList:
        fbyIdx=thisEnv.getSymbol(fbyElem.fbyIdx)
        fbyArr=thisEnv.getSymbol(fbyElem.fbyArr)
        head_content += type_change(fbyIdx.Type)+" "+fbyIdx.Name + ";\n"
        head_content += "%s %s%s;\n"%(type_change(fbyArr.Type),fbyArr.Name,getArrSize([fbyIdx.Code]))
    # automata
    if isStatemachine==1:
        head_content+="\nSSM_ST state_nxt;\n"
    head_content += "} outC_" + name + ";\n"

    #function
    head_content+="\nextern void "+name+"(inC_"+name+" *inC, outC_"+name+" *outC);\n"
    head_content+="\nextern void "+name+"_reset(outC_"+name+" *outC);\n"
    head_content += "\nextern void " + name + "_init(outC_" + name + " *outC);\n#endif"
    filename="./output/"+name+".h"
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

    #初始化函数
    c_content += "void %s_init(outC_%s *outC)\n{\n" % (name,name)
    for para in op_kind_symbol.Returns:
        symbol = thisEnv.getSymbol(para)
        realType=""
        if symbol.Type not in typeArr:
            realSymbol=getIdType(symbol.Name,thisEnv)
            realType=realSymbol.Type
        if realType == "struct":
            c_content=structInitial(c_content,"outC->"+symbol.Name,realSymbol)
        elif len(symbol.arrSize) == 0 and symbol.Kind != 'FbyArr' :
            c_content += "outC->%s=%s;\n" % (para,symbolInit(symbol,thisEnv))
    # NOTE: init状态机初始状态赋值
    if op_kind_symbol.isStatemachine:
        c_content += "outC->state_nxt=%s;\n" % op_kind_symbol.StateList[0]

    for elem in op_kind_symbol.fbyList:
        c_content += "for(int idx=0;idx<%s;idx++){\n%s[idx]=%s;\n}\n"%(objectsToString(thisEnv.getSymbol(elem.fbyIdx).Code),thisEnv.getSymbol(elem.fbyArr).changeName(None),symbolInit(thisEnv.getSymbol(elem.fbyArr),thisEnv))
    c_content += "}\n"

    #重置函数
    c_content += "void %s_reset(outC_%s *outC)\n{\n" % (name,name)
    for para in thisEnv.SymbolTable.values():
        if para.Kind=="Pre":
            c_content += "outC->%s=%s;\n"%(para.Name,symbolInit(para,thisEnv))
    # NOTE: reset状态机初始状态赋值
    if op_kind_symbol.isStatemachine:
        c_content += "outC->state_nxt=%s;\n" % op_kind_symbol.StateList[0]
    c_content += "}\n"
    filename = "./output/%s.c" %(name)
    print(c_content)
    with open(filename,'w') as f:
        f.write(c_content)

def getName(initStr):
    symbol=thisEnv.getSymbol(op_kind_id)
    for i in range(1000):
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
def symbolInit(symbol,symbolTable):
    str=""
    if len(symbol.Default)!=0:
        realType=getIdType(symbol.Name,symbolTable).Type
        setObjectsType(symbol.Default[0],realType)
        str=objectsToString(symbol.Default[0])
    elif len(symbol.Last)!=0:
        realType = getIdType(symbol.Name, symbolTable).Type
        setObjectsType(symbol.Last[0], realType)
        str = objectsToString(symbol.Last[0])
    else:
        realType = symbol.Type
        if realType in intArr:
            str="kcg_lit_%s(0)"%realType
        elif realType in floatArr:
            str="kcg_lit_%s(0.0)" % realType
        elif realType=='bool':
            str="kcg_true"
        else:
            symbolInit(getIdType(realType,thisEnv),thisEnv)
    return str

def objectsToString(objects,num=0):
    # type=""
    sstr=""
    print("objectsToString",objects)
    for elem in objects:
        print('elem.strs=',elem.strs,'elem.value=',elem.value,' ',elem.objects)
        if elem.strs=='lv6id':
            symbol=thisEnv.getSymbol(elem.value)
            # type=symbol.Type
            if len(elem.objects)!=0:
                if checkElemInStruct(symbol.Name,elem.objects,0):
                    sstr += symbol.changeName(elem.objects)
            else:
                sstr+=symbol.changeName(elem.objects)
        elif elem.strs=='integernum':
            sstr += "kcg_lit_%s(%s)" % (elem.type,str(elem.value))
        elif elem.strs=='floatnum':
            sstr+="kcg_lit_%s(%s)"%(elem.type,str(elem.value))
        elif elem.strs=='lnot_lv6id':
            sstr += "kcg_lnot_%s" % elem.type
        elif elem.strs=='true':
            sstr+="kcg_true"
        elif elem.strs=='false':
            sstr+="kcg_false"
        elif elem.strs=='enum_lv6id':
            sstr+=elem.value
        # elif elem.strs=='Pre':
        #     symbol=thisEnv.getSymbol(elem.value)
        #     symbol.Type=type
        #     sstr+=symbol.changeName()
        else:
            sstr+=elem.value
    return sstr
#存在typedef别名情况
def getIdType(symbolName,symbolTable):
    symbol=symbolTable.getSymbol(symbolName)
    if symbol!=None and symbol.Type not in typeArr:
        rootSymbolTable=getRootSymbolTable(symbolTable)
        return getIdType(symbol.Type,rootSymbolTable)
    else:
        return symbol

def getTypefromObjects(objects):
    type=""
    for obj in objects:
        if obj.strs=='lv6id':
            symbol=thisEnv.getSymbol(obj.value)
            if symbol.Type in typeArr:
                type=symbol.Type
                return type
            elif symbol.Type!='':
                rootSymbolTable=getRootSymbolTable(thisEnv)
                type=getIdType(symbol.Type,rootSymbolTable).Type
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
    return num



def getArrSize(objects):
    str=""
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

def objectsToStruct(objects):
    structRet=dict()
    for elem in objects:
        symbol=Symbol(elem[0].value,"structElem",elem[1].value)
        symbol.arrSize.extend(elem[1].objects)
        if elem[1].strs=="struct":
            symbol.FieldList=objectsToStruct(elem[1].structObjects)
        structRet[elem[0].value]=symbol
    return structRet

def getRootSymbolTable(thisEnv):
    if thisEnv.PrevTable!=None:
        return getRootSymbolTable(thisEnv.PrevTable)
    else:
        return thisEnv

#结构体赋值时需要检查结构体元素是否一致
def checkStructInitial(typeSymbol,rightObj):
    rightDict=dict()
    if(len(typeSymbol.FieldList)!=len(rightObj)):
        return False
    for idx in range(len(rightObj)):
        rightDict[rightObj[idx][0].value]=idx
    for elemK,elemV in typeSymbol.FieldList.items():
        if elemK not in rightDict:
            return False
        elif elemV.Type=='struct':
            return checkStructInitial(elemV,rightObj[rightDict[elemK]])
    return True

def structAssign(leftName,typeSymbol,rightObj,defList):
    for elem in rightObj:
        name=leftName+".%s"%(elem[0].value)
        symbol=typeSymbol.FieldList[elem[0].value]
        tmpList=list()
        if symbol.Type not in typeArr:
            realSymbol=getIdType(symbol.Type,getRootSymbolTable(thisEnv))
            if realSymbol.Type=='struct':
                if isNormalFormat(elem[1])==True:
                    structAssign(name,realSymbol,elem[1],defList)
                else:
                    tmpList.append(lex_value("","memcpy(&"+name))
                    tmpList.append(lex_value("",",&"))
                    tmpList.extend(elem[1])
                    tmpList.append(lex_value("",",sizeof("+symbol.Type+"));\n"))
                    defList.append(tmpList)
            else:
                setObjectsType(elem[1],realSymbol.Type)
                tmpList.append(lex_value("",name))
                tmpList.append(lex_value("","="))
                tmpList.extend(elem[1])
                tmpList.append(lex_value("",";\n"))
                defList.append(tmpList)
        else:
            if symbol.Type =='struct':
                if isNormalFormat(elem[1])==True:
                    structAssign(name,symbol,elem[1],defList)
                else:
                    setObjectsType(elem[1],symbol.Type)
                    tmpList.append(lex_value("", name))
                    tmpList.append(lex_value("", "="))
                    tmpList.extend(elem[1])
                    tmpList.append(lex_value("", ";\n"))
                    defList.append(tmpList)
            else:
                setObjectsType(elem[1], symbol.Type)
                tmpList.append(lex_value("", name))
                tmpList.append(lex_value("", "="))
                tmpList.extend(elem[1])
                tmpList.append(lex_value("", ";\n"))
                defList.append(tmpList)

def isNormalFormat(objects):
    if type(objects[0])==list:
        return isNormalFormat(objects[0])
    else:
        if len(objects)==1 and getIdType(objects[0].value,thisEnv).Type=='struct':
            return False
    return True

def structInitial(c_content,structName,symbol):
    if symbol.Type=="struct":
        for elemK,elemV in symbol.FieldList.items():
            if elemV.Type not in typeArr:
                rootEnv=getRootSymbolTable(thisEnv)
                realSymbol=getIdType(elemV.Type,rootEnv)
                structName+=".%s"%(elemV.Name)
                c_content=structInitial(c_content,structName,realSymbol)
            else:
                if elemV.Type !="struct":
                    c_content+="%s=%s;\n"%(structName+"."+elemV.Name,symbolInit(elemV,thisEnv))
                else:
                    structName+=".%s"%symbol.Name
                    c_content=structInitial(c_content,structName,elemV)
        return c_content

def checkType(expr1,expr2):
    type1=getTypefromObjects(expr1.objects[0])
    type2=getTypefromObjects(expr2.objects[0])
    if type1!='' and type2!='' and type1!=type2:
        print("checkType error")
        exit(0)
    elif type1=='' and type2=='':
        return
    elif type1!='' and type2=='':
        setObjectsType(expr2.objects[0],type1)
    elif type1=='' and type2!='':
        setObjectsType(expr1.objects[0],type2)
#判断params里面的元素是否是symbolName表示的结构体里面的
def checkElemInStruct(symbolName,params,idx):
    if idx >= len(params):
        return True
    realSymbol=getIdType(symbolName,thisEnv)
    if params[idx].value not in realSymbol.FieldList:
        return False
    else:
        return checkElemInStruct(realSymbol.FieldList[params[idx].value].Type,params,idx+1)

#优先级从低到高
precedence=(
    ('left','ARROW'),
    ('left','LOR','LXOR'),
    ('left','LAND'),
    ('left','OR','XOR'),
    ('left','AND'),
    ('left','EQU','NOEQU','LESSEQU','GREATEREQU','LESS','GREATER'),
    ('left','LSL','LSR'),
    ('left','PLUS','MINUS'),
    ('left','STAR','MOD','DIVIDE'),
    ('right','UMINUS','UPLUS'),
    ('left','PRE'),
    ('right','NOT','LNOT'),
    ('left','EXPONENT'),
    ('left','POINT')
)

def p_program(p):
    'Program : Decls_zero_or_more'
    # p[0]=p[1]
    pass

#not finish
def p_decls_zero_or_mode(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
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
    typeSymbol=Symbol(p[2].value,"Type",'',public,external)
    thisEnv.setSymbol(p[2].value,typeSymbol)
    if p[3].strs!='Empty':
        typeSymbol.Type=p[3].value
        if p[3].strs=='struct':
            typeSymbol.Type='struct'
            typeSymbol.FieldList=objectsToStruct(p[3].structObjects)
        elif p[3].strs=='Enum':
            typeSymbol.Type="enum"
            typeSymbol.Code.extend(p[3].objects)
        typeSymbol.arrSize.extend(p[3].objects)


def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    if len(p)==3:
        p[0]=p[2]
    else:
        p[0]=p[1]
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
    'Package_decl : Package Visibility_zero_or_one Pack_Lv6id Decls_zero_or_more END SEMICOLON'
    pass

#每一个function和node都会产生一个对应其函数名的.h和.c文件
def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    # print(p[3].value)
    global thisEnv
    symbol=thisEnv.getSymbol(p[3].value) # 该symbol名字在 User_op_decl_Lv6id已经被set
    if isStatemachine==1:
        symbol.isStatemachine=True # 该node name为状态机名字
        print('状态机', p[3].value, '的初始状态列表: ', symbol.StateList)
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

def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=p[1]
    # 上层作用域将该 id 加入自己的符号表，以备后续使用 PrevTable.getSymbol(id) 获取该符号
    global thisEnv
    symbol=Symbol(p[1].value,'OpKind')
    thisEnv.setSymbol(p[1].value,symbol)
    global op_kind_id
    op_kind_id=p[1].value

    newEnv=SymbolTable(p[1].value,thisEnv)
    thisEnv.ChildTableList.append(newEnv)
    thisEnv=newEnv
    

def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    p[0]=p[1]
    symbol=Symbol(p[1].value,'State')
    thisEnv.setSymbol(p[1].value,symbol)
    # TODO: 获取当前作用域的EnvName, 是当前状态机所属node的名字
    # 通过 thisEnv.getSymbol(thisEnv.EnvName) 得到当前状态机所属node的symbol类
    # 向该symbol中的 StateList 添加当前状态的名字
    # print("即将向当前作用域的 StateList中添加状态，This EnvName: ", thisEnv.EnvName)
    

def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0]=p[1]


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
                if len(elem.Code)==0:
                    p[0].value+="kcg_%s %s;\n"%(elem.Type,elem.Name)
                else:
                    p[0].value+="kcg_%s %s=%s;\n"%(elem.Type,elem.Name,objectsToString(elem.Code))
        if len(p)==3:
            # p[0].value+=defToString(p[1].beforeObjects)
            # p[0].value+=defToString(p[1].objects)
            # p[0].value+=defToString(p[1].afterObjects)
            # NOTE:加上Equation Control block的控制流代码
            p[0].value+=p[1].value
            print("Debug info: Opt_body len(p)==3, p[0].value is: ", p[0].value)
        else:
            # p[0].value+=defToString(p[4].beforeObjects)
            # p[0].value+=defToString(p[4].objects)
            # p[0].value+=defToString(p[4].afterObjects)
            p[0].value+=p[4].value
        # if op_kind_symbol.InitName!="":
        #     initSymbol=thisEnv.getSymbol(op_kind_symbol.InitName)
        #     p[0].value+="if(%s){%s=kcg_false;}"%(initSymbol.changeName(),initSymbol.changeName())


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
    for obj in p[2].objects:
        symbol=thisEnv.getSymbol(obj.value)
        if symbol!=None and symbol.IsReturn==True:
            thisEnv.getSymbol(op_kind_id).Returns.append(symbol.Name)


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
        p[0].value+=p[1].value+p[3].value
        # p[0].objects.extend(p[1].objects)
        # p[0].beforeObjects.extend(p[1].beforeObjects)
        # p[0].afterObjects.extend(p[1].afterObjects)
        # p[0].objects.extend(p[3].objects)
        # p[0].beforeObjects.extend(p[3].beforeObjects)
        # p[0].afterObjects.extend(p[3].afterObjects)

def p_equation(p):
    '''Equation : Simple_equation
                | Control_block Return'''
    p[0]=lex_value("Equation")
    if len(p) == 2:
        # print("Equation\n",p[0].value, ' end of p[0].value')
        # print("Equation\n",p[1].value, ' end of p[1].value')
        # p[0].objects.extend(p[1].objects)
        # p[0].beforeObjects.extend(p[1].beforeObjects)
        # p[0].afterObjects.extend(p[1].afterObjects)
        p[0].value+=defToString(p[1].beforeObjects)+defToString(p[1].objects)+defToString(p[1].afterObjects)
    elif len(p)==3: # TODO: 添加控制流等式, 改写为 objects before objects, afterObjects
        p[0].value+=p[1].value+p[2].value
        # print("Control block, p[1],p[2] value: ", p[1].value, ", ", p[2].value)


def p_control_block(p):
    '''Control_block : State_machine
    | Clocked_block'''
    p[0]=lex_value("Control_block")
    p[0].value+=p[1].value

def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0]=lex_value("Return")
    # node以及function定义的时候已经写了return的参数列表，C代码使用 outC->var_name = 为返回值赋值，所以这里的return语句不需要再生成


def p_returns_var(p):
    '''Returns_var : Returns_var_1 Returns_var_2'''
    # 目前设计 仅返回单个变量, 不能返回空变量, 这个生成式没用
    p[0]=lex_value("Returns_var")
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
    '''State_machine : AUTOMATON State_machine_1'''
    # 原来应当为 Id_zero_or_one 省略状态机名字为空的情况，默认没有ID
    print('定义状态机, 默认名字为当前node name, 即thisEnv: ', thisEnv.EnvName)
    # TODO: 添加状态机全为强迁移的情况
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
        if p[1].strs=='Weak_state_decl':
            p[0].objects.append(p[1]) # 拼接多个状态定义，每个p[i]object里面的.value字段自带代码
            p[0].objects.extend(p[2].objects)
            print('状态定义', p[1].value)
        elif p[1].strs=='Strong_state_decl':
            pass
    
def p_state_decl(p):
    '''State_decl ::= State_decl_1 State_decl_2 STATE State_Lv6id State_decl_3 Data_def State_decl_4'''
    if p[1]!=None:
        assert p[1].value == 'initial'
        print("初始状态加入状态列表！", p[4].value)
        thisNode=thisEnv.PrevTable.getSymbol(thisEnv.EnvName)
        thisNode.StateList.append(p[4].value)

    if p[7]!=None and p[7].strs=='Weak_transition':
        p[0]=lex_value("Weak_state_decl")
        # p[4] 为状态名，p[6]为状态内部赋值语句equation, p[7]为 transition
        p[0].value+='case '+p[4].value+':\n'
        p[0].value+=p[6].value+'\n'
        p[0].value+=p[7].value+'\n'
        
    elif p[5]!=None and p[5].strs=='Strong_transition':
        p[0]=lex_value("Strong_state_decl")
        # TODO: 目前仅实现弱迁移，p[5] state_decl_3 的 unless语句强迁移未实现
        
    else:
        raise NotImplementedError('状态机应当仅有强迁移或者仅有弱迁移')
    


def p_state_decl_1(p):
    '''State_decl_1 : INITIAL
                    | empty'''
    print("State_decl_1: ", p[1])
    p[0]=p[1]
    # TODO: Do something in nodename.c init, reset function
    pass

def p_state_decl_2(p):
    '''State_decl_2 : FINAL
                    | empty'''
    pass

def p_state_decl_3(p):
    '''State_decl_3 : UNLESS Strong_transition SEMICOLON
                    | empty'''
    # TODO: unless语句强迁移未实现
    p[0]=lex_value("Strong_transition")
    if len(p)>2:
        pass # 需要两个switch case，要用到objects

def p_strong_transition(p):
    '''Strong_transition : IF Expr Target'''

def p_data_def(p):
    '''Data_def : Equation SEMICOLON
                | Scope'''
    # 在状态机中仅实现了简单的无 LET...TEL语句
    p[0]=lex_value("Data_def")
    # if len(p)==5:
    #     print("Debug: 拆解状态机的arrow赋值语句, p[2].beforeObjects: ", p[2].beforeObjects)
    #     print("Debug: 拆解状态机的arrow赋值语句, p[2].objects: ", p[2].objects)
    #     print("Debug: 拆解状态机的arrow赋值语句, p[2].afterObjects: ", p[2].afterObjects)
    #     p[0].value+=defToString(p[2].beforeObjects)
    #     p[0].value+=defToString(p[2].objects)
    #     p[0].value+=defToString(p[2].afterObjects)
        # 不用额外加分号结尾
    p[0].value+=p[1].value
def p_scope(p):
    '''Scope : Signal_block_zero_or_one Local_block_zero_or_one Eqs
    | Signal_block_zero_or_one Local_block_zero_or_one'''
    p[0]=lex_value("Scope")
    if len(p)==4:
        p[0].value+=p[3].value

def p_eqs(p):
    'Eqs : LET Equation_zero_or_more_with_semicolon TEL'
    p[0]=lex_value("Eqs")
    p[0].value+=p[2].value

def p_state_decl_4(p):
    '''State_decl_4 : UNTIL Weak_transition SEMICOLON
                    | empty '''
    p[0]=lex_value("Weak_transition")
    if len(p)>2:
        p[0].value+=p[2].value

def p_weak_transition(p):
    '''Weak_transition : IF Expr Target'''
    # 省略 Scade 语法中原有的 Arrow, 因为ARROW是一个token运算符, 暂未实现 p_arrow
    print("Weak_transition: ", p[1], p[2].objects, p[3])
    p[0]=lex_value("Weak_transition")
    p[2].value = defToString(p[2].objects)

    p[0].value+="if("+p[2].value+")"
    p[0].value+="{\n  "+p[3].value+"\n}\n"
    p[0].value+='break;'

def p_target(p):
    '''Target : RESTART LV6ID'''
    # TODO: 目前仅实现 restart 关键字，状态重新开始，resume暂缓实现
    print("Target: ", p[1], p[2])
    # outC->state_nxt = state_name;
    p[0]=lex_value("Target")
    p[0].value+="outC->state_nxt = "+p[2].value+";"

    # 自底向上分析，在最底层设置全局变量, 当前node为状态机
    print('自底向上分析，在最底层设置全局变量, 当前node为状态机')
    global isStatemachine
    isStatemachine=1

def p_clocked_block(p):
    '''Clocked_block : ACTIVATE Id_zero_or_one If_block
    | ACTIVATE Id_zero_or_one Match_block'''
    #目前没发现Id_zero_or_one有什么作用
    p[0]=lex_value("Clocked_block")
    p[0].value+=p[3].value
def p_id_zero_or_one(p):
    '''Id_zero_or_one : LV6ID
    | empty'''
    pass

def p_if_block(p):
    'If_block : IF Expr THEN If_block_1 ELSE If_block_1'
    p[0]=lex_value("If_block")
    type=getTypefromObjects(p[2].objects[0])
    setObjectsType(p[2].objects[0],type)
    p[0].value+="if("+defToString(p[2].objects)+"){\n"
    p[0].value+=p[4].value
    p[0].value+="}else{\n"
    p[0].value+=p[6].value
    p[0].value+="}\n"

def p_if_block_1(p):
    '''If_block_1 : Data_def
    | If_block'''
    p[0]=lex_value("If_block_1")
    p[0].value+=p[1].value

def p_match_block(p):
    '''Match_block : WHEN Expr MATCH Match_block_1'''
    #Match_block_1的objects格式为[[[Pattern][Data_def]],[[Pattern][Data_def]],[]]
    p[0]=lex_value("Match_block")
    p[0].value+="switch("+defToString(p[2].objects)+"){\n"
    for elem in p[4].objects:
        p[0].value+="case "+elem[0][0].value+" :\n"
        p[0].value+=elem[1][0].value
        p[0].value+="break;\n"
    p[0].value+="default : \n break;\n}"


def p_match_block_1(p):
    ' Match_block_1 : VERTICALBAR Pattern COLON Data_def Match_block_2 '
    p[0]=lex_value('Match_block_1')
    patternList=list()
    patternList.append([p[2]])
    patternList.append([p[4]])
    p[0].objects.append(patternList)
    p[0].objects.extend(p[5].objects)

def p_match_block_2(p):
    '''Match_block_2 : VERTICALBAR Pattern COLON Data_def Match_block_2
    | empty'''
    p[0]=lex_value('Match_block_2')
    if len(p)==6:
        patternList = list()
        patternList.append([p[2]])
        patternList.append([p[4]])
        p[0].objects.append(patternList)
        p[0].objects.extend(p[5].objects)


def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    #若出现input1=1->pre(2)。2作为mem_pre加进符号表，此时的类型未知，初始化会出现错误。因此需要找到lhs的类型
    p[0]=lex_value('Simple_equation')
    op_kind_symbol = thisEnv.getSymbol(op_kind_id)
    if len(p[1].objects)!=len(p[3].objects):
        print("Simple_equation error")
        exit(0)
    for idx in range(len(p[1].objects)):
        #修改此处，若左边为结构体，右边是非struct_expr,则展开依次初始化
        #否则使用memcpy
        typeSymbol=getIdType(p[1].objects[idx].value,thisEnv)
        if typeSymbol.Type=="struct":
            defList=list()
            if isNormalFormat(p[3].objects[idx])==False:
                defList.append(lex_value("","memcpy(&"))
                defList.append(p[1].objects[idx])
                defList.append(lex_value("",",&"))
                defList.append(p[3].objects[idx][0])
                defList.append(lex_value("",",sizeof("+typeSymbol.Name+"));\n"))
                p[0].objects.append(defList)
            else:
                if checkStructInitial(typeSymbol,p[3].objects[idx])==False:
                    print("checkStructInitial error")
                    exit(0)
                leftName = p[1].objects[idx].value
                if thisEnv.getSymbol(p[1].objects[idx].value).IsReturn ==True:
                    leftName="outC->"+ leftName
                structAssign(leftName,typeSymbol,p[3].objects[idx],defList)
                p[0].objects.extend(defList)
        else:
            type=typeSymbol.Type
            setObjectsType(p[3].objects[idx],type)
            # if idx==0:
            #     for elem in p[3].beforeObjects:
            #         setObjectsType(elem, type)
            #     for elem in p[3].afterObjects:
            #         setObjectsType(elem,type)

            defList = list()
            defList.append(p[1].objects[idx])
            defList.append(p[2])
            defList.extend(p[3].objects[idx])
            defList.append(lex_value("", ";\n"))
            p[0].objects.append(defList)

    p[0].beforeObjects.extend(p[3].beforeObjects)
    p[0].afterObjects.extend(p[3].afterObjects)




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
        p[0].objects.extend(p[3].objects)


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
        p[0].objects.extend(p[3].objects)

def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
#直接将var_decls_2 var_decls_3 var_decls_4设置为空
    p[0]=lex_value('Var_decls')
    typeName=p[4].value
    if p[4].strs=="struct":
        #此处生成的临时结构体，作用域应在根结点的符号表内
        tmpStructName=getName("tmpStruct")
        structSymbol=Symbol(tmpStructName,'Type','struct')
        structSymbol.FieldList=objectsToStruct(p[4].structObjects)
        structSymbol.arrSize.extend(p[4].objects)
        rootSymbolTable=getRootSymbolTable(thisEnv)
        rootSymbolTable.setSymbol(tmpStructName,structSymbol)
        # print(len(thisEnv.SymbolTable))
        typeName=tmpStructName

    symbol = thisEnv.getSymbol(p[1].value)
    symbol.Type = typeName
    symbol.arrSize.extend(p[4].objects)
    if p[7].strs!='Empty':
        symbol.Last.extend(p[7].objects)
        symbol.IsReturn=True
        # thisEnv.getSymbol(op_kind_id).Returns.append(symbol.Name)
    for i in range(len(p[2].objects)):
        symbol=thisEnv.getSymbol(p[2].objects[i].value)
        symbol.Type=typeName
        symbol.arrSize.extend(p[4].objects)
        if p[7].strs!='Empty':
            symbol.Last.extend(p[7].objects)
            symbol.IsReturn=True
            # thisEnv.getSymbol(op_kind_id).Returns.append(symbol.Name)

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
    '''Var_decls_4 : Last_decl
    | empty'''
    p[0]=p[1]

def p_last_decl(p):
    '''Last_decl : LAST EQU Expr'''
    p[0]=lex_value("Last_decl")
    p[0].objects.extend(p[3].objects)

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
    if p[4].strs=='struct': #若为结构体，则是const imported c12:{tt1:bool,tt2:float32};
        #创建一个变量，该symbol的Kind为type，结构体定义在kcg_types.h文件里
        type=getName('tmpStruct')
        typeSymbol=Symbol(type,"Type",'struct')
        thisEnv.setSymbol(type,typeSymbol)
        typeSymbol.FieldList=objectsToStruct(p[4].structObjects)
    else:
        type=p[4].value
    if len(p)==7:
        #此处关于结构体的初始化还没有完成
        symbol=Symbol(p[2].value,'Const',type,public,external,isPackage,packageName)
        symbol.arrSize.extend(p[4].objects)
        setObjectsType(p[6].objects[0],type)
        symbol.FieldList=objectsToStruct(p[4].structObjects)
        symbol.Code=p[6].objects[0]
        thisEnv.setSymbol(p[2].value,symbol)
    elif len(p)==5:
        symbol=Symbol(p[2].value,'Const',type,public,external,isPackage,packageName)
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
        if p[3].strs=='struct':
            typeName=getName("tmpStruct")
            typeSymbol=Symbol(typeName,"Type",'struct')
            thisEnv.setSymbol(typeName,typeSymbol)
            typeSymbol.FieldList=objectsToStruct(p[3].structObjects)
        else:
            typeName=p[3].value
        symbol=Symbol(item.value,'Sensor')
        symbol.Type=typeName
        thisEnv.setSymbol(item.value,symbol)
        symbol.arrSize.extend(p[3].objects)


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
    | Path_id Type_expr_2
    | LBPARENTHESE Field_decl Type_expr_1 RBPARENTHESE Type_expr_2'''
    #Type_expr_2表示是否是数组
    p[0]=lex_value('')
    if len(p)==3:
        p[0].strs=p[1].strs
        p[0].value=p[1].value
        if len(p[2].objects)!=0:
            p[0].objects.extend(p[2].objects)
    elif p[1].strs=='signed' or p[1].strs=='unsigned':
        #没写完，需要将INTCONST改为Expr
        #需要计算出Expr表达式代表的值，Expr可能是静态数组，结构体。
        #该情况也可能出现数组，没有完成
        # num=exprToNum(p[3].objects)
        if p[1].strs=='signed':
            type="int"+str(p[3].value)
        elif p[1].strs=='unsigned':
            type="uint"+str(p[3].value)
        p[0].strs=type
        p[0].value=p[1].value
    elif p[1].strs=='{':
        #structObjects表示结构体的每个元素[[[lex_value("lv6id")],[type_expr]]]
        #objects指示其是否是数组
        p[0].strs="struct"
        p[0].objects.extend(p[5].objects)
        p[0].structObjects.extend(p[2].objects)
        p[0].structObjects.extend(p[3].objects)
def p_type_expr_1(p):
    '''Type_expr_1 : COMMA Field_decl Type_expr_1
    | empty'''
    if len(p)!=2:
        p[0]=lex_value("Type_expr_1")
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
    else:
        p[0]=p[1]

def p_field_decl(p):
    '''Field_decl : LV6ID COLON Type_expr'''
    p[0]=lex_value("Field_decl")
    field=list()
    field.append(p[1])
    if p[3].strs=="struct":
        tmpStructName=getName("tmpStruct")
        structSymbol=Symbol(tmpStructName,'Type','struct')
        structSymbol.FieldList=objectsToStruct(p[3].structObjects)
        structSymbol.arrSize.extend(p[3].objects)
        rootSymbolTable=getRootSymbolTable(thisEnv)
        rootSymbolTable.setSymbol(tmpStructName,structSymbol)
        tmpLex_value=lex_value("struct",tmpStructName)
        tmpLex_value.structObjects.extend(p[3].structObjects)
        tmpLex_value.objects.extend(p[3].objects)
        field.append(tmpLex_value)
    else:
        field.append(p[3])
    p[0].objects.append(field)


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
    if p[2]!=None and len(p[2].objects)!=0:
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
        symbol=thisEnv.getSymbol(p[3].value)
        if symbol !=None:
            p[0].objects.append(p[3])
        else:
            realType=getIdType(p[3].value,thisEnv)
            lastName = getName("lastTmp")
            lastSymbol = Symbol(lastName, "TmpVar", realType.Type)
            thisEnv.setSymbol(lastName, lastSymbol)
            p[0].objects.append(lex_value("lv6id", lastName))
            lastSymbol.Code.append(p[3])
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
    | Bool_expr
    | Struct_expr'''
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
        if len(p[1].objects)!=len(p[3].objects):
            print("tempo_expr arrow:error")
            exit()

        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)

        for idx in range(len(p[1].objects)):
            initName=getName("init")
            initSymbol=Symbol(initName,"Init","bool")
            initSymbol.IsReturn=True
            thisEnv.setSymbol(initName,initSymbol)
            symbol.Returns.append(initName)

            # initName = symbol.InitName     # FIXME: 'init变量不会自增' BUG
            initElem = getName("initElem")
            initLex = lex_value("initElem", initElem)
            thisEnv.setSymbol(initElem, Symbol(initElem, "TmpVar"))
            befDefList = list()
            befDefList.extend([lex_value("if(", "if(", "str"), lex_value("lv6id", initName), lex_value("){\n", "){\n")])
            befDefList.extend([lex_value("lv6id", initElem), lex_value("=", "=")])
            befDefList.extend(p[1].objects[idx])
            befDefList.append(lex_value("",";\n"))
            befDefList.extend([lex_value("lv6id",initName),lex_value("=","="),lex_value("","kcg_false;\n")])
            befDefList.append(lex_value("", "}else{\n"))
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
        if len(p[3].objects)!=len(p[7].objects):
            print("tempo_expr fby:error")
            exit()

        p[0].beforeObjects += p[3].beforeObjects + p[5].beforeObjects + p[7].beforeObjects
        p[0].afterObjects += p[3].afterObjects + p[5].afterObjects + p[7].afterObjects
        for idx in range(len(p[3].objects)):
            initName=getName("init")
            initSymbol=Symbol(initName,"Init","bool")
            initSymbol.IsReturn=True
            thisEnv.setSymbol(initName,initSymbol)
            symbol.Returns.append(initName)


            fbyIdx = getName("fbyIdx")
            fbyArr = getName("fbyArray")

            type = getTypefromObjects(p[5].objects[0])
            if type == "":
                type = "int32"
            fbyIdxSymbol = Symbol(fbyIdx, "FbyIdx", type)
            fbyIdxSymbol.IsReturn = True
            fbyArrSymbol = Symbol(fbyArr, "FbyArr")
            fbyArrSymbol.IsReturn = True
            fbyArrSymbol.IsArray = True
            thisEnv.setSymbol(fbyIdx, fbyIdxSymbol)
            thisEnv.setSymbol(fbyArr, fbyArrSymbol)
            fbyIdxSymbol.Code.extend(p[5].objects[0])
            setObjectsType(fbyIdxSymbol.Code, type)
            symbol.Returns.append(fbyIdx)
            symbol.Returns.append(fbyArr)
            symbol.fbyList.append(fbyClass(fbyIdx, fbyArr))

            p[0].objects.append(
                [lex_value("lv6id", fbyArr, ""), lex_value("[", "[", "str"), lex_value("lv6id", fbyIdx, "int32"),
                 lex_value("]", "]", "str")])

            befDefList = list()

            befDefList.extend([lex_value("", "if("), lex_value("lv6id", initName),
                               lex_value(")\n{\n", ")\n{\n")])
            befDefList.append(lex_value("", "for(int idx=0;idx<%s;idx++){\n" % objectsToString(p[5].objects[0])))
            befDefList.extend([lex_value("lv6id", fbyArr), lex_value("", "["), lex_value("", "idx"), lex_value("", "]=")])
            befDefList.extend(p[7].objects[idx])
            befDefList.append(lex_value("",";\n}\n"))

            befDefList.extend([lex_value("lv6id",initName),lex_value("","="),lex_value("","kcg_false;\n")])
            befDefList.extend([lex_value("lv6id",fbyIdx),lex_value("","="),lex_value("","0;\n")])
            befDefList.append(lex_value("", "}\n"))
            p[0].beforeObjects.append(befDefList)


            aftDefList = list()
            aftDefList.extend(
                [lex_value("lv6id", fbyArr), lex_value("", "["), lex_value("lv6id", fbyIdx), lex_value("", "]=")])
            aftDefList.extend(p[3].objects[idx])
            aftDefList.append(lex_value("", ";\n"))
            aftDefList.extend(
                [lex_value("lv6id", fbyIdx), lex_value("", "=("), lex_value("lv6id", fbyIdx), lex_value("", "+1)%(")])
            aftDefList.extend(p[5].objects[0])
            aftDefList.append(lex_value("", ");\n"))
            p[0].afterObjects.append( aftDefList)

        # for elem in p[0].beforeObjects:
        #     print("fby",elem)

def p_relation_expr(p):
    '''Relation_expr : Expr EQU Expr
    | Expr NOEQU Expr
    | Expr LESS Expr
    | Expr GREATER Expr
    | Expr LESSEQU Expr
    | Expr GREATEREQU Expr'''

    p[0]=lex_value("Relation_expr")
    if p[2].strs=='<>':
        p[2].value='!='
    elif p[2].strs=='=':
        p[2].value='=='
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].beforeObjects.extend(p[3].beforeObjects)

    if len(p[1].objects)!=len(p[3].objects) and len(p[1].objects)!=1:
        print("relation_epxr:error")
        exit(0)
    checkType(p[1],p[3])
    p[0].objects.append(lex_value("","("))
    p[0].objects.extend(p[1].objects[0])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects[0])
    p[0].objects.append(lex_value("",")"))

    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].afterObjects.extend(p[3].afterObjects)

# def p_bin_relation_op(p):
#     '''Bin_relation_op : EQU
#     | NOEQU
#     | LESS
#     | GREATER
#     | LESSEQU
#     | GREATEREQU'''
#     p[0]=p[1]
#     if p[1].strs=='<>':
#         p[0].value='!='
#     elif p[1].strs=='=':
#         p[0].value='=='


def judgeIsEnum(objects):
    symName=""
    for elem in objects:
        if elem.strs=='lv6id':
            symbol=thisEnv.getSymbol(elem.value)
            if symbol!=None:
                value=symbol.Type
                while value not in typeArr:#存在该变量的类型是重命名之后，因此需要找到该变量的最初类型
                    symbol=thisEnv.getSymbol(value)
                    value=symbol.Type
                symName=symbol.Name
    return symName


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
        elif elem[0][0].strs=='enum_lv6id':
            eDict[elem[0][0].value]-=1
    for key,value in eDict.items():
        if value==1:
            sum+=1
    if (sum>=1 and isUnderline==True) or (sum==0 and isUnderline==False):
        return True
    return False

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
        symName=judgeIsEnum(p[3].objects[0])
        exprSymbol=thisEnv.getSymbol(symName)
        if exprSymbol==None:
            print("Switch_expr Error")
            exit(0)
        if exprSymbol.Type=="enum":
            if checkEnum(exprSymbol.Name,p[5].objects[0])==False:
                print("Switch_expr enum Error")
                exit(0)
        for idx in range(len(p[5].objects)):
            caseName=getName("caseTmp")
            caseSymbol=Symbol(caseName,"TmpVar")
            thisEnv.setSymbol(caseName,caseSymbol)
            defList=list()
            defList.append(lex_value("","switch("))
            defList.extend(p[3].objects[0])
            defList.append(lex_value("","){\n"))
            for elem in p[5].objects[idx]:
                if elem[0][0].value!='_':
                    defList.append(lex_value("", "case "))
                    defList.extend(elem[0])
                else:
                    isDefault=True
                    defList.append(lex_value("","default "))
                defList.append(lex_value("", " :\n"))
                defList.append(lex_value("lv6id", caseName))
                defList.append(lex_value("", " = "))
                defList.extend(elem[1])
                defList.append(lex_value("", ";\nbreak;\n"))
            if isDefault==False:
                defList.append(lex_value("","default :\nbreak;\n}\n"))
            else:
                defList.append(lex_value("","}\n"))
            p[0].beforeObjects.append(defList)
            p[0].objects.append([lex_value("lv6id", caseName)])


def p_switch_expr_1(p):
    'Switch_expr_1 : Case_expr Switch_expr_2'
    p[0]=lex_value('Switch_expr_1')
    for idx in range(len(p[1].objects)):
        p[0].objects.append([p[1].objects[idx]])
    for idx in range(len(p[2].objects)):
        p[0].objects[idx].extend(p[2].objects[idx])
def p_switch_expr_2(p):
    '''Switch_expr_2 : Case_expr Switch_expr_2
    | empty'''
    p[0]=lex_value("Switch_expr_2")
    if len(p)==3:
        for idx in range(len(p[1].objects)):
            p[0].objects.append([p[1].objects[idx]])
        for idx in range(len(p[2].objects)):
            p[0].objects[idx].extend(p[2].objects[idx])

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
    if len(p)==3:
        p[0]=p[2]
        p[2].value=str(-p[2].value)
    else:
        p[0]=p[1]
        if p[0].strs=='lv6id':
            p[0].strs='enum_lv6id'

def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
    p[0]=p[1]

#Arith_expr还要添加(Expr:Type_expr) 文法
def p_arith_expr(p):
    '''Arith_expr : LPARENTHESE Expr COLON Type_expr RPARENTHESE'''
    p[0]=lex_value("Arith_expr")
    realType=p[4].value
    if realType not in typeArr:
        realType=getIdType(p[4].value,getRootSymbolTable(thisEnv)).Type
    p[0].objects.append(lex_value("","(kcg_%s)"%(realType)))
    if len(p[2].objects[0])!=1:
        p[0].objects.append(lex_value("","("))
    setObjectsType(p[2].objects[0],realType)
    p[0].objects.extend(p[2].objects[0])

    if len(p[2].objects[0]) != 1:
        p[0].objects.append(lex_value("", ")"))

def p_arith_expr_unary(p):
    '''Arith_expr : MINUS Expr %prec UMINUS
    | PLUS Expr %prec UPLUS
    | LNOT Expr'''
    p[0]=lex_value("Arith_expr")
    p[0].beforeObjects.extend(p[2].beforeObjects)
    type=getTypefromObjects(p[2].objects[0])
    setObjectsType(p[2].objects[0],type)
    if p[1].strs == '-':
        p[0].objects.append(lex_value("", "("))
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects[0])
        p[0].objects.append(lex_value("", ")"))
    elif p[1].strs == 'lnot':
        # 新增一个变量，将其strs设置为lnot_lv6id。当遍历到这个变量时，将其转化为kcg_lnot_type
        p[0].objects.extend([lex_value("lnot_lv6id"), lex_value("(", "(")])
        p[0].objects.extend(p[2].objects[0])
        p[0].objects.append(lex_value(")", ")"))
    p[0].afterObjects.extend(p[2].afterObjects)
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
    p[0] = lex_value("Arith_expr")
    checkType(p[1],p[3])
    if p[2].strs=='mod':
        p[2].value=' % '
    elif p[2].strs=='land':
        p[2].value=' & '
    elif p[2].strs=='lor':
        p[2].value=' | '
    elif p[2].strs == 'lxor':
        p[2].value = ' ^ '
    elif p[2].strs=='lsl':
        p[2].value=' << '
    elif p[2].strs=='lsr':
        p[2].value=' >> '
    print("Arith_expr:",p[1].objects,p[3].objects,p[2].strs)
    p[0].objects.append(lex_value("", "("))
    p[0].objects.extend(p[1].objects[0])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects[0])
    p[0].objects.append(lex_value("", ")"))
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].beforeObjects.extend(p[3].beforeObjects)
    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].afterObjects.extend(p[3].afterObjects)


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

#typed_integer和typed_float未添加
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
    | HASHTAG LPARENTHESE List RPARENTHESE'''
    p[0]=lex_value("Bool_expr")
    if len(p)==3:
        p[1].value='!'
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects[0])
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
    elif len(p)==5:
        for idx in range(len(p[3].objects)):
            p[0].objects.append(lex_value("","("))
            p[0].objects.extend(p[3].objects[idx])
            p[0].objects.append(lex_value("", ")"))
            if idx!=len(p[3].objects)-1:
                p[0].objects.append(lex_value("","+"))
        p[0].objects.append(lex_value("","<=1"))

def p_bool_expr_bin(p):
    '''Bool_expr : Expr AND Expr
    | Expr OR Expr
    | Expr XOR Expr'''
    p[0]=lex_value('Bool_expr')
    if p[2].strs=='and':
        p[2].value=' & '
    elif p[2].strs=='or':
        p[2].value=' | '
    elif p[2].strs=='xor':
        p[2].value=' ^ '
    p[0].objects.append(lex_value("", "("))
    p[0].objects += p[1].objects[0]
    p[0].objects.append(p[2])
    p[0].objects += p[3].objects[0]
    p[0].objects.append(lex_value("", ")"))
    p[0].beforeObjects += p[1].beforeObjects + p[3].beforeObjects
    p[0].afterObjects += p[1].afterObjects + p[3].afterObjects
# def p_bin_bool_op(p):
#     '''Bin_bool_op : AND
#     | OR
#     | XOR'''
#     if p[1].strs=='and':
#         p[1].value=' & '
#     elif p[1].strs=='or':
#         p[1].value=' | '
#     elif p[1].strs=='xor':
#         p[1].value=' ^ '
#     p[0]=p[1]

def p_struct_expr(p):
    '''Struct_expr : Expr POINT LV6ID
    | LBPARENTHESE Label_expr Struct_expr_1 RBPARENTHESE'''
    p[0]=lex_value("Struct_expr")
    if len(p)==5:
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
    elif len(p)==4:
        idx1=len(p[1].objects)-1
        idx2=len(p[1].objects[idx1])-1
        p[1].objects[idx1][idx2].objects.append(p[3])
        p[0].objects.extend(p[1].objects[0])
        print("Sturct_expr",p[1].objects[idx1],p[1].objects[idx1][idx2],p[1].objects[idx1][idx2].objects)
        # print("Struct_expr",p[1].objects,type(p[1].objects[0][0]))
def p_struct_expr_1(p):
    '''Struct_expr_1 : COMMA Label_expr Struct_expr_1
    | empty'''
    p[0]=lex_value("Struct_expr_1")
    if len(p)!=2:
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)

def p_label_expr(p):
    '''Label_expr : LV6ID COLON Expr'''
    p[0]=lex_value("Label_expr")
    p[0].beforeObjects.extend(p[3].beforeObjects)
    p[0].afterObjects.extend(p[3].afterObjects)
    labelList=list()
    labelList.append(p[1])
    labelList.extend(p[3].objects)
    p[0].objects.append(labelList)

def p_error(p):
    print("Syntax error in input!")

def p_empty(p):
    'empty :'
    p[0]=lex_value('Empty')

def get_parse(strs):
    global program
    parser=yacc(debug=1)
    parse=yacc(debug=1)
    pattern = r'\#[\w]+'
    strs=re.sub(pattern,'',strs)
    print("=======strs=====\n",strs)
    string_tokens=get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes=parser.parse(strs,lexer=scade_lexer)
    return program,GlobalEnv

if __name__=='__main__':
    parser=yacc(debug=1)
    strs = """
    node simple_automaton (i: int32; c: bool; d: bool) returns (o: int32)
    automaton
        state ADD1
        let
            o = 100 -> i + 1 ;
        tel
        until if c and d restart MINUS1;

        initial state MINUS1
        let
            o = 2 -> i - 1 ;
        tel
        until if c or d restart ADD1;
    returns o; 
    """
    # strs = """
    # node strong_automaton (i: int32; c: bool; d: bool) returns (o: int32)
    # automaton
    #     state ADD1
    #     unless if c and d restart MINUS1;
    #     let
    #         o = 100 -> i + 1 ;
    #     tel
    #
    #     initial state MINUS1
    #     unless if c restart ADD1;
    #     let
    #         o = 2 -> i - 1 ;
    #     tel
    # returns o;
    # """
    
    string_tokens=get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes=parser.parse(strs,lexer=scade_lexer)
    print(nodes)


