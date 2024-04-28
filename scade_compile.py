import copy

from ply.yacc import yacc
# from scade_lex import scade_lex, get_tokens, tokens, lex_value
from SymbolClass import Symbol, SymbolTable, fbyClass
import re
from scade_compile_otherFunc import *

isPackage = 0
# global isStatemachine
isStatemachine = 0

packageName = ""
op_kind_id = ""
op_kind = ""

scade_lexer = scade_lex()
GlobalEnv = SymbolTable('Global')  #global的符号表中的符号为各个函数的函数名，该符号只填充了Returns,Params,isStatemachine,hasInternalState
                                   #global的符号表中还有子符号表，名为其子函数名的符号表。
thisEnv = GlobalEnv
program = None

# 全局变量，用于存储被调用过的函数名称
# calledOperators = []


def type_change(type):
    list = ["char", "bool", "float32", "float64", "size", "uint64", "uint32", "uint16", "uint8", "int64", "int32",
            "int16", "int8"]
    str = type
    if type in list:
        str = "kcg_" + type
    return str


def generate_head_file(symtable):
    op_kind_symbol = symtable.PrevTable.getSymbol(symtable.EnvName)
    name = op_kind_symbol.Name
    head_content = ""
    head_content += "#ifndef _" + name + "_H_\n" + "#define _" + name + "_H_\n"
    head_content += "#include \"kcg_types.h\"\n\n"
    head_content += "typedef struct {\n"
    # input_params
    # print(len(op_kind_symbol.Params))
    for input_name in op_kind_symbol.Params:
        symbol = symtable.getSymbolInThisEnv(input_name)
        head_content += "%s %s%s;\n" % (type_change(symbol.Type), input_name, getArrSize(symbol.arrSize))
    head_content += "} inC_" + name + ";\n"

    # out_params
    head_content += "\n\ntypedef struct {\n"
    for key,symbol in symtable.SymbolTable.items():
        if symbol.IsReturn == True:
            if symbol.Kind == 'FbyIdx' or symbol.Kind == 'FbyArr':
                continue
            else:
                head_content += "%s %s%s;\n"%(type_change(symbol.Type),key,getArrSize(symbol.arrSize))

    for fbyElem in op_kind_symbol.fbyList:
        fbyIdx = symtable.getSymbolInThisEnv(fbyElem.fbyIdx)
        fbyArr = symtable.getSymbolInThisEnv(fbyElem.fbyArr)
        head_content += type_change(fbyIdx.Type) + " " + fbyIdx.Name + ";\n"
        head_content += "%s %s%s;\n" % (type_change(fbyArr.Type), fbyArr.Name, getArrSize([fbyIdx.Code]))
    # automata
    if op_kind_symbol.isStatemachine == 1:
        head_content += "\nSSM_ST state_nxt;\n"
    head_content += "} outC_" + name + ";\n"

    # function
    head_content += "\nextern void " + name + "(inC_" + name + " *inC, outC_" + name + " *outC);\n"
    head_content += "\nextern void " + name + "_reset(outC_" + name + " *outC);\n"
    head_content += "\nextern void " + name + "_init(outC_" + name + " *outC);\n#endif"
    filename = "./output/" + name + ".h"
    print(head_content)
    with open(filename, 'w') as f:
        f.write(head_content)


def generate_c_file(body,symtable):
    globalSymbol = symtable.PrevTable.getSymbol(symtable.EnvName)
    c_content = "#include \"kcg_consts.h\"\n#include \"kcg_sensors.h\"\n"
    c_content += "#include \"macro_libmathext64.h\"\n"
    name = globalSymbol.Name
    c_content += "#include \"%s.h\"\n" % name
    for callOperator in globalSymbol.callOperators:
        c_content += "#include \"%s.h\"\n" % callOperator
    c_content += "void %s(inC_%s *inC, outC_%s *outC)\n{\n" % (name, name, name)
    c_content += body
    c_content += "\n}\n"

    # 初始化函数
    c_content += "void %s_init(outC_%s *outC)\n{\n" % (name, name)
    for key,symbol in symtable.SymbolTable.items():
        if symbol.IsReturn==True:
            realType = ""
            if symbol.Type not in typeArr:
                realSymbol=getIdType(key,symtable)
                realType=realSymbol.Type
            if len(symbol.arrSize)!=0:
                tmpName=len(symbol.arrSize)-1
                tmpName2=''
                for idx in reversed(symbol.arrSize):
                    c_content+="for(kcg_size idx%s=0;idx%s<%s;idx%s++){\n"%(tmpName,tmpName,idx[0].value,tmpName)
                    tmpName2+='[idx%s]'%(tmpName)
                    tmpName=tmpName-1
                if realType=="struct":
                    c_content=structInitial(c_content,"outC->%s%s"%(symbol.Name,tmpName2),realSymbol)
                elif symbol.Kind!='FbyArr':
                    c_content+="outC->%s%s=%s;\n"%(key,tmpName2,symbolInit(symbol,symtable))
                for idx in range(len(symbol.arrSize)):
                    c_content+="}\n"
            else:
                if realType == "struct":
                    c_content = structInitial(c_content, "outC->" + symbol.Name, realSymbol)
                elif len(symbol.arrSize) == 0 and symbol.Kind != 'FbyArr':
                    c_content += "outC->%s=%s;\n" % (key, symbolInit(symbol, symtable))
    # NOTE: init状态机初始状态赋值
    if globalSymbol.isStatemachine:
        c_content += "outC->state_nxt=%s;\n" % globalSymbol.initState

    for elem in globalSymbol.fbyList:
        c_content += "for(int idx=0;idx<%s;idx++){\n%s[idx]=%s;\n}\n" % (
            objectsToString(symtable.getSymbolInThisEnv(elem.fbyIdx).Code, symtable,op_kind_id),
            symtable.getSymbolInThisEnv(elem.fbyArr).changeName(symtable),
            symbolInit(symtable.getSymbolInThisEnv(elem.fbyArr), symtable))
    c_content += "}\n"

    # 重置函数
    c_content += "void %s_reset(outC_%s *outC)\n{\n" % (name, name)
    for para in symtable.SymbolTable.values():
        if para.Kind == "Pre":
            c_content += "outC->%s=%s;\n" % (para.Name, symbolInit(para, symtable))
    # NOTE: reset状态机初始状态赋值
    if globalSymbol.isStatemachine:
        c_content += "outC->state_nxt=%s;\n" % globalSymbol.initState
    c_content += "}\n"
    filename = "./output/%s.c" % (name)
    print(c_content)
    with open(filename, 'w') as f:
        f.write(c_content)

# Generate Head file for called operators
def generate_head_file_for_called_operator(symtable):
    print("symtable.EnvName=",symtable.EnvName," symtable.PrevTable=",symtable.PrevTable.EnvName)
    op_kind_symbol=symtable.PrevTable.getSymbolInThisEnv(symtable.EnvName)
    name=op_kind_symbol.Name
    head_content=""
    head_content+="#ifndef _"+name+"_H_\n"+"#define _"+name+"_H_\n"
    head_content+="#include \"kcg_types.h\"\n\n"
    
    if op_kind_symbol.hasInternalState == True:
        head_content += "\n\ntypedef struct {\n"
        for elem in symtable.SymbolTable.values():
            if elem.IsReturn == True:
                if elem.Kind == 'FbyIdx' or elem.Kind == 'FbyArr':
                    continue
                else:
                    head_content+="%s %s%s;\n"%(type_change(elem.Type),elem.Name,getArrSize(elem.arrSize))
        for fbyElem in op_kind_symbol.fbyList:
            fbyIdx = symtable.getSymbolInThisEnv(fbyElem.fbyIdx)
            fbyArr = symtable.getSymbolInThisEnv(fbyElem.fbyArr)
            head_content += type_change(fbyIdx.Type) + " "+fbyIdx.Name +";\n"
            head_content += "%s %s%s;\n" % (type_change(fbyArr.Type), fbyArr.Name, getArrSize([fbyIdx.Code]))
        if op_kind_symbol.isStatemachine == 1:
            head_content += "\nSSM_ST state_nxt;\n"
        head_content += "} outC_" + name + ";\n"
    else:
        print("function")

    if op_kind_symbol.hasInternalState == False and len(op_kind_symbol.Returns)==1:
        retSymbol=symtable.getSymbolInThisEnv(op_kind_symbol.Returns[0])
        head_content += "extern %s %s("%(type_change(retSymbol.Type),name)
    else:
        head_content+="extern void %s("%name

    #input_params
    for input_name in op_kind_symbol.Params:
        symbol = symtable.getSymbolInThisEnv(input_name)
        if input_name != op_kind_symbol.Params[0]:
            head_content += "," + type_change(symbol.Type) + " " + input_name
        else:
            head_content += type_change(symbol.Type) + " " + input_name
        
    if op_kind_symbol.hasInternalState == True:
        head_content += ",outC_" + name +" *outC"
    else:
        if len(op_kind_symbol.Returns)!=0:
            for output_name in op_kind_symbol.Returns:
                symbol=symtable.getSymbolInThisEnv(output_name)
                head_content += ","+type_change(symbol.Type) +" *" + symbol.Name
    head_content+=");\n"

    # endif 
    head_content += "#endif\n"
    
    filename="./output/"+name+".h"
    print(head_content)
    with open(filename,'w') as f:
        f.write(head_content)

# Generate C file for called operators
def generate_c_file_for_called_operator(body,symtable):
    op_kind_symbol = symtable.PrevTable.getSymbolInThisEnv(symtable.EnvName)
    c_content = "#include \"kcg_consts.h\"\n#include \"kcg_sensors.h\"\n"
    c_content += "#include \"macro_libmathext64.h\"\n"
    name = op_kind_symbol.Name
    c_content += "#include \"%s.h\"\n" % name
    
    if op_kind_symbol.hasInternalState == False and len(op_kind_symbol.Returns)==1:
        returnSymbol=symtable.getSymbolInThisEnv(op_kind_symbol.Returns[0])
        c_content +="%s %s("%(type_change(returnSymbol.Type),name)
    else:
        c_content += "void %s("%name

    #input_params
    for input_name in op_kind_symbol.Params:
        symbol = symtable.getSymbolInThisEnv(input_name)
        if input_name != op_kind_symbol.Params[0]:
            c_content += "," + type_change(symbol.Type) + " " + input_name
        else:
            c_content += type_change(symbol.Type) + " " + input_name
    if op_kind_symbol.hasInternalState == True:
        c_content += ",outC_"+ name + " *outC"
    else:
        if len(op_kind_symbol.Returns)!=1:
            for output_name in op_kind_symbol.Returns:
                c_content += ","+type_change(symbol.Type) + " *" + output_name
    c_content += ")\n{\n"

    c_content += body 
    if op_kind_symbol.hasInternalState == False and len(op_kind_symbol.Returns)==1:
        c_content+="return %s;"%op_kind_symbol.Returns[0]
    c_content += "\n}\n"

     # 初始化函数
    c_content += "void %s_init(outC_%s *outC)\n{\n" % (name, name)
    for key,symbol in symtable.SymbolTable.items():
        if symbol.IsReturn==True:
            realType = ""
            if symbol.Type not in typeArr:
                realSymbol=getIdType(key,symtable)
                realType=realSymbol.Type
            if len(symbol.arrSize)!=0:
                tmpName=len(symbol.arrSize)-1
                tmpName2=''
                for idx in reversed(symbol.arrSize):
                    c_content+="for(kcg_size idx%s=0;idx%s<%s;idx%s++){\n"%(tmpName,tmpName,idx[0].value,tmpName)
                    tmpName2+='[idx%s]'%(tmpName)
                    tmpName=tmpName-1
                if realType=="struct":
                    c_content=structInitial(c_content,"outC->%s%s"%(symbol.Name,tmpName2),realSymbol)
                elif symbol.Kind!='FbyArr':
                    c_content+="outC->%s%s=%s;\n"%(key,tmpName2,symbolInit(symbol,symtable))
                for idx in range(len(symbol.arrSize)):
                    c_content+="}\n"
            else:
                if realType == "struct":
                    c_content = structInitial(c_content, "outC->" + symbol.Name, realSymbol)
                elif len(symbol.arrSize) == 0 and symbol.Kind != 'FbyArr':
                    c_content += "outC->%s=%s;\n" % (key, symbolInit(symbol, symtable))
    # NOTE: init状态机初始状态赋值
    if op_kind_symbol.isStatemachine:
        c_content += "outC->state_nxt=%s;\n" % op_kind_symbol.initState

    for elem in op_kind_symbol.fbyList:
        c_content += "for(int idx=0;idx<%s;idx++){\n%s[idx]=%s;\n}\n" % (
            objectsToString(symtable.getSymbolInThisEnv(elem.fbyIdx).Code, symtable,op_kind_id),
            symtable.getSymbolInThisEnv(elem.fbyArr).changeName(symtable),
            symbolInit(symtable.getSymbolInThisEnv(elem.fbyArr), symtable))
    c_content += "}\n"

    # 重置函数
    c_content += "void %s_reset(outC_%s *outC)\n{\n" % (name, name)
    for para in symtable.SymbolTable.values():
        if para.Kind == "Pre":
            c_content += "outC->%s=%s;\n" % (para.Name, symbolInit(para, symtable))
    # NOTE: reset状态机初始状态赋值
    if op_kind_symbol.isStatemachine:
        c_content += "outC->state_nxt=%s;\n" % op_kind_symbol.initState
    c_content += "}\n"

    filename = "./output/%s.c" %(name)
    print(c_content)
    with open(filename,'w') as f:
        f.write(c_content)



def getName(initStr):
    symbol = thisEnv.getSymbolInThisEnv(op_kind_id)
    for i in range(1000):
        target = initStr
        if i != 0:
            target += str(i)
        # if target in symbol.Params or target in symbol.Returns or target in symbol.StaticParams:
        #     continue
        # else:
        #     return target
        if target in thisEnv.SymbolTable:
            continue
        else:
            return target
    return initStr


def symbolInit(symbol, symbolTable):
    str = ""
    if len(symbol.Default) != 0:
        realType = getIdType(symbol.Name, symbolTable).Type
        setObjectsType(symbol.Default[0], realType)
        str = objectsToString(symbol.Default[0], thisEnv,op_kind_id)
    elif len(symbol.Last) != 0:
        realType = getIdType(symbol.Name, symbolTable).Type
        setObjectsType(symbol.Last[0], realType)
        str = objectsToString(symbol.Last[0], thisEnv,op_kind_id)
    else:
        realType = symbol.Type
        if realType in intArr:
            str = "kcg_lit_%s(0)" % realType
        elif realType in floatArr:
            str = "kcg_lit_%s(0.0)" % realType
        elif realType == 'bool':
            str = "kcg_true"
        else:
            symbolInit(getIdType(realType, thisEnv), thisEnv)
    return str


def getTypefromObjects(objects):
    type = ""
    for obj in objects:
        if obj.strs == 'lv6id' and len(obj.objects)==0:
            symbol = thisEnv.getSymbolInThisEnv(obj.value)
            if symbol.Type in typeArr:
                type = symbol.Type
                return type
            elif symbol.Type != '':
                rootSymbolTable = getRootSymbolTable(thisEnv)
                type = getIdType(symbol.Type, rootSymbolTable).Type
        elif obj.strs=='lv6id' and len(obj.objects)!=0:
            type=getStructElemType(obj,thisEnv).Type
    return type


def setObjectsType(objects, type):
    for elem in objects:
        symbol = thisEnv.getSymbolInThisEnv(elem.value)
        if symbol == None:
            if elem.type == '':
                elem.type = type
        else:
            if symbol.Type == '':
                symbol.Type = type


def exprToNum(objects):
    # 逆波兰表达式得到值
    num = 0
    for elem in objects:
        if elem.strs == 'lv6id':
            symbol = thisEnv.getSymbolInThisEnv(elem.value)
    return num




def defToString(defList):
    content = ""
    for elem in defList:
        content += objectsToString(elem, thisEnv,op_kind_id)
    return content


def objectsToStruct(objects):
    structRet = dict()
    for elem in objects:
        symbol = Symbol(elem[0].value, "structElem", elem[1].value)
        symbol.arrSize.extend(elem[1].arrSize)
        if elem[1].strs == "struct":
            symbol.FieldList = objectsToStruct(elem[1].objects)
        structRet[elem[0].value] = symbol
    return structRet


# 结构体赋值时需要检查结构体元素是否一致
def checkStructInitial(typeSymbol, rightObj):
    rightDict = dict()
    if (len(typeSymbol.FieldList) != len(rightObj)):
        return False
    for idx in range(len(rightObj)):
        rightDict[rightObj[idx][0].value] = idx
    for elemK, elemV in typeSymbol.FieldList.items():
        if elemK not in rightDict:
            return False
        elif elemV.Type == 'struct':
            return checkStructInitial(elemV, rightObj[rightDict[elemK]])
    return True


def structAssign(leftLex,leftSymbol, typeSymbol, elem):
    leftLex.objects.append(elem[0])
    symbol = typeSymbol.FieldList[elem[0].value]
    if symbol.Type not in typeArr:
        symbol = getIdType(symbol.Type, getRootSymbolTable(thisEnv))
    if symbol.Type == 'struct':
        if isNormalFormat(elem[1]) == True:
            for obj in elem[1]:
                structAssign(leftLex, leftSymbol,symbol, obj)
        else:
            #此处使用memcpy
            tmpName=""
            for idx in range(len(leftLex.objects)):
                tmpName+=leftLex.objects[idx].value
                if idx!=len(leftLex.objects)-1:
                    tmpName+="."
            type=getStructElemType(leftLex,thisEnv).Type
            leftLex.type=type
            print("memcpy setObjectsType=",elem[1]," type",type)
            setObjectsType(elem[1],type)
            leftSymbol.StateType='struct'
            elemSymbol=Symbol()
            elemSymbol.StateType='memcpy'
            elemSymbol.Code.extend(elem[1])
            leftSymbol.FieldValueList[tmpName]=elemSymbol
    else:
        #此处使用依次赋值
        tmpName=""
        for idx in range(len(leftLex.objects)):
            tmpName+=leftLex.objects[idx].value
            if idx!=len(leftLex.objects)-1:
                tmpName+="."
        typeSymbol=getStructElemType(leftLex,thisEnv)
        
        elemSymbol=Symbol()
        leftSymbol.StateType='struct'
        leftLex.type=typeSymbol.Type
        if len(typeSymbol.arrSize)!=0:  #结构体元素是数组
            arrSizeList=getArrSizeList(typeSymbol.arrSize)
            for obj in elem[1]:
                setObjectsType(obj,typeSymbol.Type)
            elemSymbol.StateType='arrayList'
            elemSymbol.arrSize=typeSymbol.arrSize
            fillArrValueList(elem[1],arrSizeList,0,elemSymbol.arrValueList,typeSymbol)
        else:
            setObjectsType(elem[1],typeSymbol.Type)
            elemSymbol.StateType='equation'
            elemSymbol.Code.extend(elem[1])
        # setObjectsType(elem[1],typeSymbol.Type)
        # leftLex.type=typeSymbol.Type
        # elemSymbol.StateType='equation'
        # elemSymbol.Code.extend(elem[1])
        leftSymbol.FieldValueList[tmpName]=elemSymbol

    leftLex.objects.pop()


def isNormalFormat(objects):
    print("isNormalFormat",objects)
    if type(objects[0]) == list:
        return isNormalFormat(objects[0])
    else:
        if len(objects) == 1 and getIdType(objects[0].value, thisEnv).Type == 'struct':
            return False
    return True


def structInitial(c_content, structName, symbol):
    if symbol.Type == "struct":
        for elemK, elemV in symbol.FieldList.items():
            if elemV.Type not in typeArr:
                rootEnv = getRootSymbolTable(thisEnv)
                realSymbol = getIdType(elemV.Type, rootEnv)
                structName += ".%s" % (elemV.Name)
                c_content = structInitial(c_content, structName, realSymbol)
            else:
                if elemV.Type != "struct":
                    c_content += "%s=%s;\n" % (structName + "." + elemV.Name, symbolInit(elemV, thisEnv))
                else:
                    structName += ".%s" % symbol.Name
                    c_content = structInitial(c_content, structName, elemV)
        return c_content


def checkType(expr1, expr2, idx):
    type1 = getTypefromObjects(expr1.objects[idx])
    type2 = getTypefromObjects(expr2.objects[idx])
    if type1 != '' and type2 != '' and type1 != type2:
        raise NotImplementedError("checkType error")
    elif type1 == '' and type2 == '':
        return type1
    elif type1 != '' and type2 == '':
        setObjectsType(expr2.objects[0], type1)
        return type1
    elif type1 == '' and type2 != '':
        setObjectsType(expr1.objects[0], type2)
        return type2
    else:
        return type1


# 优先级从低到高
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
    symDicts=dict()
    for elem in thisEnv.ChildTableList:
        symDicts[elem.EnvName]=elem
    for obj in p[1].objects:
        text=""
        symtable=symDicts[obj[0].value]
        print("======",symtable.EnvName)
        for elem in symtable.SymbolTable.values():
            if elem.Kind == "LocalVar":
                text += "%s %s;\n"%(type_change(elem.Type),elem.Name)
            if elem.Kind=="TmpVar":
                if elem.StateType != 'equation':
                    text += "%s %s;\n" % (type_change(elem.Type), elem.Name)
                else:
                    text += "%s %s=%s;\n" % (type_change(elem.Type), elem.Name, objectsToString(elem.Code, symtable,symtable.EnvName))
        for elem in obj[1].objects:
            text+=typeToString(elem[1],[elem[0]],symtable,symtable.EnvName)
        nodeSymbol=thisEnv.getSymbol(obj[0].value)
        print("nodeSymbol.isCalled=",nodeSymbol.isCalled)
        if nodeSymbol.isCalled:
            generate_head_file_for_called_operator(symtable)
            generate_c_file_for_called_operator(text,symtable)
        else:
            generate_head_file(symtable)
            generate_c_file(text,symtable)           


# not finish
def p_decls_zero_or_mode(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''
    # p[0]=p[1]+p[2]
    # pass
    p[0]=lex_value("Decls_zero_or_more")
    if len(p)==3:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)


# not finish
def p_decls(p):
    '''Decls : Const_block
    | Type_block
    | Sensor_block
    | Package_decl
    | User_op_decl'''
    # p[0]=p[1]
    p[0]=lex_value("Decls")
    if p[1]!=None:
        p[0].objects.extend(p[1].objects)


def p_type_block(p):
    'Type_block : TYPE Type_block_1'
    pass


def p_type_block_1(p):
    '''Type_block_1 : Type_decl SEMICOLON Type_block_1
                    | empty'''
    pass


def p_Type_decl(p):
    'Type_decl : Interface_status LV6ID Type_decl_1 Type_decl_2'
    external = True
    public = True
    if len(p[1].objects) == 1:
        external = False
    if p[1].objects[0].value == "private":
        public = False
    typeSymbol = Symbol(p[2].value, "Type", '', public, external)
    thisEnv.setSymbol(p[2].value, typeSymbol)
    if p[3].strs != 'Empty':
        typeSymbol.Type = p[3].value
        if p[3].strs == 'struct':
            typeSymbol.Type = 'struct'
            typeSymbol.FieldList = objectsToStruct(p[3].objects)
        elif p[3].strs == 'Enum':
            typeSymbol.Type = "enum"
            typeSymbol.Code.extend(p[3].objects)
        typeSymbol.arrSize.extend(p[3].arrSize)


def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[1]


def p_type_decl_2(p):
    '''Type_decl_2 : IS Numeric_kind
                   | empty'''
    pass


def p_type_def(p):
    '''Type_def : Type_expr
                | ENUM LBPARENTHESE Id_one_or_more_with_comma RBPARENTHESE'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[3]
        p[0].strs = 'Enum'


def p_numeric_kind(p):
    '''Numeric_kind : NUMERIC
    | FLOAT
    | INTEGER
    | SIGNED
    | UNSIGNED'''
    pass


# 将LV6ID写成Lv6id是为了提前知道包的名字
def p_package_decl(p):
    'Package_decl : Package Visibility_zero_or_one Pack_Lv6id Decls_zero_or_more END SEMICOLON'
    pass


# 每一个function和node都会产生一个对应其函数名的.h和.c文件
def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    p[0]=lex_value("User_op_decl")
    global thisEnv
    globalSymbol = thisEnv.PrevTable.getSymbol(p[3].value)  # 该symbol名字在 User_op_decl_Lv6id已经被set
    localSymbol=thisEnv.getSymbolInThisEnv(p[3].value)
    if isStatemachine == 1:
        localSymbol.isStatemachine = True  # 该node name为状态机名字
    for idx in p[5].objects:
        # print(idx.strs,idx.value)
        globalSymbol.Params.append(idx.value)
    for idx in p[7].objects:
        globalSymbol.Returns.append(idx.value)
    # if symbol.isCalled:
    #     generate_head_file_for_called_operator()
    #     generate_c_file_for_called_operator(p[10].value)
    # else:
    #     generate_head_file()
    #     generate_c_file(p[10].value)
    p[0].objects.append([p[3],p[10]])
    thisEnv = thisEnv.PrevTable


def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0] = p[1]


def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0] = p[1]
    # 上层作用域将该 id 加入自己的符号表，以备后续使用 PrevTable.getSymbol(id) 获取该符号
    global thisEnv
    symbol = Symbol(p[1].value, 'OpKind')
    if op_kind == 'node':
        symbol.hasInternalState=True
    thisEnv.setSymbol(p[1].value, symbol)
    global op_kind_id
    op_kind_id = p[1].value

    newEnv = SymbolTable(p[1].value, thisEnv)
    thisEnv.ChildTableList.append(newEnv)
    thisEnv = newEnv


def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    p[0] = p[1]
    symbol = Symbol(p[1].value, 'State')
    thisEnv.setSymbol(p[1].value, symbol)
    # TODO: 获取当前作用域的EnvName, 是当前状态机所属node的名字
    # 通过 thisEnv.getSymbol(thisEnv.EnvName) 得到当前状态机所属node的symbol类
    # 向该symbol中的 StateList 添加当前状态的名字
    # print("即将向当前作用域的 StateList中添加状态，This EnvName: ", thisEnv.EnvName)


def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    #若为node，则表示函数内部和时序相关。函数调用时，返回值使用结构体。否则，返回值一个时，直接return，多个，使用指针。
    p[0] = p[1]
    global op_kind
    op_kind=p[1].value


def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL'''
    p[0] = lex_value("Opt_body")
    if len(p) == 2:
        pass
    else:
        if len(p) == 3:
            # NOTE:加上Equation Control block的控制流代码
            # p[0].value += p[1].value
            p[0].objects.append([p[1],thisEnv.getSymbolInThisEnv(p[1].value)])
            # print("Debug info: Opt_body len(p)==3, p[0].value is: ", p[0].value)
        else:
            symbolList = []
            tmpDict={}
            for elem in p[4].objects:
                symbol = thisEnv.getSymbolInThisEnv(elem.value)
                if symbol != None:
                    tmpDict[symbol]=elem
                    if symbol.StateType=='arrayList':
                        for elem in symbol.arrValueList:
                            getRely(elem,thisEnv,symbol.relyList)
                    elif symbol.StateType=='ApplyExpr':
                        for retVal in symbol.Returns:
                            retSymbol=thisEnv.getSymbolInThisEnv(retVal.value)
                            getRely(symbol,thisEnv,symbol.relyList)
                    else:
                        getRely(symbol,thisEnv,symbol.relyList)
                    symbolList.append(symbol)
            symbolList = topologyReady(symbolList)
            for symbol in symbolList:
                leftLex=tmpDict[symbol]
                p[0].objects.append([leftLex,symbol])


def p_signal_block_zero_or_one(p):
    '''Signal_block_zero_or_one : empty'''
    pass


def p_local_block_zero_or_one(p):
    '''Local_block_zero_or_one : Local_block
    | empty'''
    # p[0] = p[1]
    pass


def p_local_block(p):
    '''Local_block : VAR Local_block_1'''
    pass


def p_local_block_1(p):
    '''Local_block_1 : Var_decls SEMICOLON Local_block_1
    | empty'''
    p[0] = lex_value("Local_block_1")
    if len(p) == 4:
        for elem in p[1].objects:
            symbol=thisEnv.getSymbolInThisEnv(elem.value)
            symbol.Kind='LocalVar'
        for elem in p[3].objects:
            symbol=thisEnv.getSymbolInThisEnv(elem.value)
            symbol.Kind='LocalVar'


def p_equation_zero_or_more_with_semicolon(p):
    '''Equation_zero_or_more_with_semicolon : Equation SEMICOLON Equation_zero_or_more_with_semicolon
    | empty'''
    p[0] = lex_value("Equation_zero_or_more_with_semicolon")
    if len(p) == 4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[3].objects)
        p[0].value += p[1].value + p[3].value


def p_equation(p):
    '''Equation : Simple_equation
                | Control_block Return'''
    p[0] = lex_value("Equation")
    # 在此处创建拓扑排序所需的类
    if len(p) == 2:
        p[0].strs = 'Simple_equation'
        p[0].objects.extend(p[1].objects)
    elif len(p) == 3:  # TODO: 添加控制流等式, 改写为 objects before objects, afterObjects
        p[0].strs = 'Control_block'
        p[0].objects.extend(p[1].objects)
        p[0].value += p[1].value + p[2].value
        # print("Control block, p[1],p[2] value: ", p[1].value, ", ", p[2].value)

def p_control_block(p):
    '''Control_block : State_machine
    | Clocked_block'''
    p[0] = lex_value("Control_block")
    p[0].value += p[1].value
    if p[1].strs=='Clocked_block':
        p[0].objects.extend(p[1].objects)


def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0] = lex_value("Return")
    # node以及function定义的时候已经写了return的参数列表，C代码使用 outC->var_name = 为返回值赋值，所以这里的return语句不需要再生成


def p_returns_var(p):
    '''Returns_var : Returns_var_1 Returns_var_2'''
    # 目前设计 仅返回单个变量, 不能返回空变量, 这个生成式没用
    p[0] = lex_value("Returns_var")
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
    p[0] = lex_value("State_machine")

    if p[2].strs == 'Weak_state_machine':
        # switch (state_sel)
        p[0].value += "SSM_ST state_sel = outC->state_nxt;\n"
        p[0].value += "switch (state_sel)\n{\n"
        for statement in p[2].objects:  # 每个状态已经在生成式中构造好了数据流和状态转移语句
            p[0].value += statement.value + "\n"
        p[0].value += "}\n"
    elif p[2].strs == 'Strong_state_machine':
        p[0].value += "SSM_ST state_act;\n"
        p[0].value += "SSM_ST state_sel = outC->state_nxt;\n"
        p[0].value += "switch (state_sel)\n{\n"
        for statement in p[2].beforeObjects:  # NOTE: beforeObjects 用来装强迁移的state_act条件赋值
            p[0].value += statement.value + "\n"
        p[0].value += "}\n"

        p[0].value += "switch (state_act)\n{\n"
        for statement in p[2].afterObjects:
            p[0].value += statement.value + "\n"
        p[0].value += "}\n"
    else:
        raise NotImplementedError('状态机定义为空，语法错误')


def p_state_machine_1(p):
    '''State_machine_1 : State_decl State_machine_1
                       | empty'''
    p[0] = lex_value("State_machine_1")
    if len(p) == 3:
        if p[1].strs == 'Weak_state_decl':
            p[0].strs = 'Weak_state_machine'
            p[0].objects.append(p[1])  # 拼接多个状态定义，每个p[i]object里面的.value字段自带代码
            p[0].objects.extend(p[2].objects)
            print('状态定义', p[1].value)

        elif p[1].strs == 'Strong_state_decl':
            p[0].strs = 'Strong_state_machine'
            p[0].beforeObjects.extend(p[1].beforeObjects)
            p[0].beforeObjects.extend(p[2].beforeObjects)
            p[0].afterObjects.extend(p[1].afterObjects)
            p[0].afterObjects.extend(p[2].afterObjects)
            print('状态定义', p[1].value)


def p_state_decl(p):
    '''State_decl ::= State_decl_1 State_decl_2 STATE State_Lv6id State_decl_3 Data_def State_decl_4'''
    thisNode = thisEnv.PrevTable.getSymbolInThisEnv(thisEnv.EnvName)
    if p[1] != None and p[1].strs != 'Empty':
        assert p[1].value == 'initial'
        print("记录初始状态", p[4].value)
        thisNode.initState = p[4].value

    # NOTE: 将状态添加至该状态机的状态列表中, 默认状态不会有重复名称
    thisNode.StateList.append(p[4].value)

    if p[7] != None and p[7].strs == 'Weak_transition':
        if thisNode.StrongOrWeak == 1:
            raise NotImplementedError('已出现过unless语句，当前状态机应当仅有强迁移, p[7]:', p[7])
        p[0] = lex_value("Weak_state_decl")
        # p[4] 为状态名，p[6]为状态内部赋值语句equation, p[7]为 weak transition
        p[0].value += 'case ' + p[4].value + ':\n{\n'
        p[0].value += p[6].value + '\n'
        p[0].value += p[7].value + '\n}\n'

    elif p[5] != None and p[5].strs == 'Strong_transition':
        print("检测到强迁移语句, p[4]: ", p[4], ", p[5]: ", p[5].beforeObjects, ", p[6]:", p[6], ", p[7]:", p[7])
        if thisNode.StrongOrWeak == 0:
            raise NotImplementedError('已出现过until语句，当前状态机应当仅有弱迁移')
        p[0] = lex_value("Strong_state_decl")
        # p[5].value 是强迁移的条件转移, p[6].value是状态内部赋值语句equation
        # state_sel第一个switch case, 放到 beforeObjects; 对应的 strong_transition 生成式需要写 strong_target
        switch_case_first = lex_value("switch_case_first")
        switch_case_first.value += "case " + p[4].value + ":\n{\n"
        switch_case_first.value += p[5].beforeObjects[0].value + "\n}\n"  # 先进行状态转移
        p[0].beforeObjects.append(switch_case_first)

        # state_act 第二个 switch case放到afterObjects
        switch_case_second = lex_value("switch_case_second")
        switch_case_second.value += "case " + p[4].value + ":\n{\n"
        switch_case_second.value += p[6].value + "\n"  # 状态内部赋值语句
        switch_case_second.value += "outC->state_nxt = state_act;\n"  # 更新state_nxt
        switch_case_second.value += "break;\n}\n"
        p[0].afterObjects.append(switch_case_second)

    else:
        print("分析状态机错误, p[4]:", p[4], "，p[5]:", p[5], ", p[6]:", p[6], ", p[7]:", p[7])
        raise NotImplementedError('状态迁移定义语法错误')


def p_state_decl_1(p):
    '''State_decl_1 : INITIAL
                    | empty'''
    print("State_decl_1: ", p[1])
    p[0] = p[1]
    pass


def p_state_decl_2(p):
    '''State_decl_2 : FINAL
                    | empty'''
    pass


def p_state_decl_3(p):
    '''State_decl_3 : UNLESS Strong_transition SEMICOLON
                    | empty'''
    thisNode = thisEnv.PrevTable.getSymbolInThisEnv(thisEnv.EnvName)
    if len(p) > 2:  # thisNode.StrongOrWeak==None
        thisNode.StrongOrWeak = 1
        p[0] = lex_value("Strong_transition")
        print("State_decl_3: ", p[1], p[2], p[3])
        if len(p) > 2:
            p[0].beforeObjects.append(p[2])  # strong_transition obj value已转换成代码


def p_strong_transition(p):
    '''Strong_transition : IF Expr Strong_target'''
    print("Strong_transition: ", p[1], p[2].objects, p[3])
    p[0] = lex_value("Strong_transition")
    p[2].value = defToString(p[2].objects)

    p[0].value += "if(" + p[2].value + ")"
    p[0].value += "{\n  " + p[3].value + "\n}\n"
    p[0].value += "else {\n"
    p[0].value += "state_act = state_sel;\n}\n"
    p[0].value += "break;"


def p_strong_target(p):
    '''Strong_target : RESTART LV6ID'''
    # TODO: 目前仅实现 restart 关键字，状态重新开始，resume暂缓实现
    print("Strong_target: ", p[1], p[2])
    p[0] = lex_value("Strong_target")
    p[0].value += "state_act = " + p[2].value + ";"

    global isStatemachine
    isStatemachine = 1


def p_data_def(p):
    '''Data_def : Equation SEMICOLON
                | Scope'''
    # 在状态机中仅实现了简单的无 LET...TEL语句
    p[0] = lex_value("Data_def")
    # if len(p)==5:
    #     print("Debug: 拆解状态机的arrow赋值语句, p[2].beforeObjects: ", p[2].beforeObjects)
    #     print("Debug: 拆解状态机的arrow赋值语句, p[2].objects: ", p[2].objects)
    #     print("Debug: 拆解状态机的arrow赋值语句, p[2].afterObjects: ", p[2].afterObjects)
    #     p[0].value+=defToString(p[2].beforeObjects)
    #     p[0].value+=defToString(p[2].objects)
    #     p[0].value+=defToString(p[2].afterObjects)
    p[0].objects = p[1].objects


def p_scope(p):
    '''Scope : Signal_block_zero_or_one Local_block_zero_or_one Eqs
    | Signal_block_zero_or_one Local_block_zero_or_one'''
    p[0] = lex_value("Scope")
    for elem in p[2].objects:
        symbol = thisEnv.getSymbolInThisEnv(elem.value)
        p[0].value += "kcg_%s %s;\n" % (symbol.Type, symbol.Name)
    if len(p) == 4:
        p[0].objects = p[3].objects


def p_eqs(p):
    'Eqs : LET Equation_zero_or_more_with_semicolon TEL'
    p[0] = p[2]


def p_state_decl_4(p):
    '''State_decl_4 : UNTIL Weak_transition SEMICOLON
                    | empty '''
    print("State_decl_4:", p[1])
    thisNode = thisEnv.PrevTable.getSymbolInThisEnv(thisEnv.EnvName)
    if len(p) > 2:
        thisNode.StrongOrWeak = 0
        p[0] = lex_value("Weak_transition")
        if len(p) > 2:
            p[0].value += p[2].value


def p_weak_transition(p):
    '''Weak_transition : IF Expr Weak_target'''
    # 省略 Scade 语法中原有的 Arrow, 因为ARROW是一个token运算符, 暂未实现 p_arrow
    print("Weak_transition: ", p[1], p[2].objects, p[3])
    p[0] = lex_value("Weak_transition")
    p[2].value = defToString(p[2].objects)

    p[0].value += "if(" + p[2].value + ")"
    p[0].value += "{\n  " + p[3].value + "\n}\n"
    p[0].value += 'break;'


def p_weak_target(p):
    '''Weak_target : RESTART LV6ID'''
    # TODO: 目前仅实现 restart 关键字，状态重新开始，resume暂缓实现
    print("Weak_target: ", p[1], p[2])
    # outC->state_nxt = state_name;
    p[0] = lex_value("Weak_target")
    p[0].value += "outC->state_nxt = " + p[2].value + ";"

    # 自底向上分析，在最底层设置全局变量, 当前node为状态机
    print('自底向上分析，在最底层设置全局变量, 当前node为状态机')
    global isStatemachine
    isStatemachine = 1


def p_clocked_block(p):
    '''Clocked_block : ACTIVATE Id_zero_or_one If_block
    | ACTIVATE Id_zero_or_one Match_block'''
    # 目前没发现Id_zero_or_one有什么作用。activate块为局部块，可以为其新建一个符号表，Id_zero_or_one为其符号表的标识。
    p[0] = lex_value("Clocked_block")
    # p[0].value += p[3].value
    if p[3].strs=='If_block':
        for elem in p[3].objects:
            p[0].objects.append(elem[0])
    else:
        p[0].objects.extend(p[3].objects)

def p_id_zero_or_one(p):
    '''Id_zero_or_one : LV6ID
    | empty'''
    pass


def p_if_block(p):
    'If_block : IF Expr THEN If_block_1 ELSE If_block_1'
    p[0] = lex_value("If_block")
    for elem in p[4].objects:
        symbol = thisEnv.getSymbolInThisEnv(elem[0].value)
        symbol.StateType = 'ifCondition'
        flag = False
        for nextElem in p[6].objects:
            if nextElem[0].value == symbol.Name:
                tmpList = list()
                ifNode = Node('ifCondition')
                ifNode.childNodeList.append(elem[1])
                ifNode.childNodeList.append(nextElem[1])
                ifNode.value.extend(p[2].objects[0])
                symbol.Code.append(ifNode)
                flag = True
                tmpList.append(elem[0])
                tmpList.append(ifNode)
                p[0].objects.append(tmpList)
                break
        if flag == False:
            ifNode = Node('ifCondition')
            ifNode.childNodeList.append(elem[1])
            ifNode.value.extend(p[2].objects[0])
            symbol.Code.append(ifNode)
            tmpList = list()
            tmpList.append(elem[0])
            tmpList.append(ifNode)
            p[0].objects.append(tmpList)
    for elem in p[6].objects:
        flag=False
        for nextElem in p[4].objects:
            if nextElem[0].value==elem[0].value:
                flag=True
        if flag==False:
            symbol=thisEnv.getSymbolInThisEnv(elem[0].value)
            symbol.StateType='ifCondition'
            ifNode=Node('ifCondition')
            ifNode.childNodeList.append(elem[1])
            valueObjects=[lex_value("","!")]
            valueObjects.extend(p[2].objects[0])
            ifNode.value.extend(valueObjects)
            symbol.Code.append(ifNode)
            p[0].objects.append([elem[0],ifNode])


def p_if_block_1(p):
    '''If_block_1 : Data_def
    | If_block'''
    p[0] = lex_value()
    p[0].strs = p[1].strs
    if p[1].strs == 'Data_def':
        for elem in p[1].objects:
            tmplist = list()
            symbol = thisEnv.getSymbolInThisEnv(elem.value)
            if symbol != None:
                tmplist.append(elem)
                if symbol.StateType=='ifCondition' or symbol.StateType=='switchCondition':
                    tmplist.append(symbol.Code[0])
                else:
                    ifNode = Node(symbol.StateType)
                    ifNode.value.extend(symbol.Code)
                    tmplist.append(ifNode)
                # else:
                #     ifNode.value.extend(symbol.Code)
                #     print("data_def= symbol.Code=",symbol.Code," symbol.Name=",symbol.Name)
                # ifNode.value.extend(symbol.Code)
                symbol.Code.clear()
            p[0].objects.append(tmplist)
    else:
        p[0]=p[1]
        for elem in p[1].objects:
            symbol=thisEnv.getSymbolInThisEnv(elem[0].value)
            if symbol!=None:
                symbol.Code.clear()


def p_match_block(p):
    '''Match_block : WHEN Expr MATCH Match_block_1'''
    # Match_block_1的objects格式为[[[Pattern][Data_def]],[[Pattern][Data_def]],[]]
    p[0] = lex_value("Match_block")
    for elem in p[4].objects:
        symbol=thisEnv.getSymbolInThisEnv(elem[0][0].value)
        if symbol!=None:
            switchNode=Node('switchCondition')
            switchNode.value.extend(p[2].objects[0])
            switchNode.childNodeList.extend(elem[1])

            symbol.StateType='switchCondition'
            symbol.Code.append(switchNode)
            p[0].objects.extend(elem[0])


def p_match_block_1(p):
    ' Match_block_1 : VERTICALBAR Pattern COLON Data_def1 Match_block_2 '
    p[0] = lex_value('Match_block_1')
    tmpDict = {}
    for elem in p[4].objects:
        tmpList=list()
        symbol=thisEnv.getSymbolInThisEnv(elem[0][0].value)
        if symbol!=None:
            if elem[0][0].type=='ifCondition' or elem[0][0].type=='switchCondition':
                tmpList.append(elem[0])
                tmpList.append(elem[1])
                elem[1][0].pattern.append(p[2])
            else:
                tmpNode = Node(elem[0][0].type)
                tmpNode.pattern.append(p[2])
                tmpNode.value.extend(elem[1])

                tmpList.append(elem[0])
                tmpList.append([tmpNode])
            p[0].objects.append(tmpList)
            tmpDict[symbol.Name] = len(p[0].objects) - 1
    if len(p[5].objects)!=0:
        for elem in p[5].objects:
            if elem[0][0].value in tmpDict.keys():
                idx=tmpDict[elem[0][0].value]
                p[0].objects[idx][1].extend(elem[1])
            else:
                p[0].objects.append([elem[0], elem[1]])
    # patternList = list()
    # patternList.append([p[2]])
    # patternList.append([p[4]])
    # p[0].objects.append(patternList)
    # p[0].objects.extend(p[5].objects)


def p_match_block_2(p):
    '''Match_block_2 : VERTICALBAR Pattern COLON Data_def1 Match_block_2
    | empty'''
    p[0] = lex_value('Match_block_2')
    if len(p)==6:
        tmpDict={}
        for elem in p[4].objects:
            tmpList=list()
            symbol=thisEnv.getSymbolInThisEnv(elem[0][0].value)
            if symbol!=None:
                if elem[0][0].type=='ifCondition' or elem[0][0].type=='switchCondition':
                    tmpList.append(elem[0])
                    tmpList.append(elem[1])
                    elem[1][0].pattern.append(p[2])
                else:
                    tmpNode = Node(elem[0][0].type)
                    tmpNode.pattern.append(p[2])
                    tmpNode.value.extend(elem[1])

                    tmpList.append(elem[0])
                    tmpList.append([tmpNode])
                p[0].objects.append(tmpList)
                tmpDict[symbol.Name]=len(p[0].objects)-1

        if len(p[5].objects)!=0:
            for elem in p[5].objects:
                if elem[0][0].value in tmpDict.keys():
                    idx=tmpDict[elem[0][0].value]
                    p[0].objects[idx][1].extend(elem[1])
                else:
                    p[0].objects.append([elem[0],elem[1]])

#为了避免symbol的Code被覆盖
def p_data_def_1(p):
    'Data_def1 : Data_def'
    p[0]=lex_value('Data_def1')
    for elem in p[1].objects:
        tmpList=list()
        symbol=thisEnv.getSymbolInThisEnv(elem.value)
        if symbol!=None:
            elem.type=symbol.StateType
            tmpList.append([elem])
            tmpList.append(copy.deepcopy(symbol.Code))
            symbol.Code.clear()
            # if elem.type=='ifBlock' or elem.type=='switchBlock':
            #     if elem.type=='ifBlock':
            #         print("Data_def1=",symbol.ifTree.type,symbol.ifTree.value,symbol.ifTree.left,symbol.ifTree.right)
            #     tmpList.append([copy.deepcopy(symbol.ifTree)])
            #     symbol.ifTree=None
            # else:
            #     tmpList.append(copy.deepcopy(symbol.Code))
            #     symbol.Code.clear()
            p[0].objects.append(tmpList)

def fillArrValueList(objects,arrSizeList,st,arrValueList,typeSymbol):
    if st>=len(arrSizeList):
        if typeSymbol.Type=='struct':
            if isNormalFormat(objects)==False:
                symbol=Symbol()
                symbol.Code.extend(objects)
                symbol.StateType='memcpy'
                arrValueList.append(symbol)
            else:
                if checkStructInitial(typeSymbol,objects)==False:
                    raise NotImplementedError()
                symbol=Symbol()
                for elem in objects:
                    structAssign(lex_value("lv6id",typeSymbol.Name),symbol,typeSymbol,elem)
                arrValueList.append(symbol)
        else:
            symbol=Symbol()
            symbol.Code.extend(objects)
            symbol.StateType='equation'
            arrValueList.append(symbol)
        return
    for idx in range(arrSizeList[st]):
        print("fill",objects[idx],"arrSizeList[st]=",arrSizeList[st])
        fillArrValueList(objects[idx],arrSizeList,st+1,arrValueList,typeSymbol)

def isApplyExpr(lex_lists):
    for idx in range(len(lex_lists)):
        if lex_lists[idx].type=="ApplyExpr":
            symbol=thisEnv.PrevTable.getSymbolInThisEnv(lex_lists[idx].value)
            return True,symbol,idx
    return False,None,-1

def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    # 若出现input1=1->pre(2)。2作为mem_pre加进符号表，此时的类型未知，初始化会出现错误。因此需要找到lhs的类型
    p[0] = lex_value('Simple_equation')

    leftIdx=0
    #此时等式左边，右边都是列表类型
    for idx in range(len(p[3].objects)):
        # 修改此处，若左边为结构体，右边是非struct_expr,则展开依次初始化
        # 否则使用memcpy
        typeSymbol = getIdType(p[1].objects[leftIdx].value, thisEnv)
        leftSymbol=thisEnv.getSymbolInThisEnv(p[1].objects[leftIdx].value)
        arrSizeList=getArrSizeList(leftSymbol.arrSize)
        isApply,applySym,opLexIdx=isApplyExpr(p[3].objects[idx])#applySym表示对应的函数在全局所对应的符号
        if isApply:
            opSym=thisEnv.getSymbolInThisEnv(p[3].objects[idx][opLexIdx].value)#表示在该env下函数名所对应的符号
            if applySym.hasInternalState == True:
                outStrucName=getName("tmpStruct")
                outSymbol=Symbol(outStrucName,"TmpVar","outC_"+opSym.Name)
                thisEnv.setSymbol(outStrucName,outSymbol)
                opSym.Returns.append(lex_value('',outStrucName))
                opSym.StateType='ApplyExpr'
                p[0].objects.append(lex_value("lv6id",opSym.Name))
                for elem in applySym.Returns:
                    leftSymbol=thisEnv.getSymbolInThisEnv(p[1].objects[leftIdx].value)
                    leftSymbol.StateType='equation'
                    leftSymbol.Code.extend([lex_value("","outC_"),lex_value("lv6id",opSym.Name),lex_value("","."),lex_value("",elem)])
                    p[0].objects.append(p[1].objects[leftIdx])
                    leftIdx+=1
            else:
                if len(applySym.Returns)==1:
                    leftSymbol.StateType='equation'
                    leftSymbol.Code.extend(p[3].objects[idx])
                    p[0].objects.append(p[1].objects[leftIdx])
                    leftIdx+=1
                else:
                    opSym.StateType='ApplyExpr'
                    for _ in applySym.Returns:
                        opSym.Returns.append(p[1].objects[leftIdx])
                        leftIdx+=1
                    p[0].objects.append(p[3].objects[idx][opLexIdx])               
            continue
        if len(arrSizeList)!=0:
            if p[3].strs=='Array_list_expr':
                leftSymbol.StateType='arrayList'
                fillArrValueList(p[3].objects[idx],arrSizeList,0,leftSymbol.arrValueList,typeSymbol)
                p[0].objects.append(p[1].objects[leftIdx])
            else:
                #使用memcpy
                print("memcpy")
                leftSymbol.StateType='memcpy'
                leftSymbol.Code.extend(p[3].objects[idx])
                p[0].objects.append(p[1].objects[leftIdx])
            leftIdx+=1
        else:
            if typeSymbol.Type == "struct":
                if isNormalFormat(p[3].objects[idx]) == False:
                #此处需要使用memcpy,等式两边都是明确的结构体类型
                    leftSymbol.Code.extend(p[3].objects[idx])
                    leftSymbol.StateType='memcpy'
                    p[0].objects.append(p[1].objects[leftIdx])
                else:
                    # 检测等式左右两边变量结构体是否一致
                    #此处需要依次初始化。
                    if checkStructInitial(typeSymbol, p[3].objects[idx]) == False:
                        raise NotImplementedError("checkStructInitial error")
                    for elem in p[3].objects[idx]:
                        # 结构体的元素放在lex_value()的objects中
                        structAssign(p[1].objects[leftIdx], leftSymbol,typeSymbol, elem)
                    p[0].objects.append(p[1].objects[leftIdx])
                leftIdx+=1
            else:
                type = typeSymbol.Type
                setObjectsType(p[3].objects[idx], type)
                setObjectsType(p[3].beforeObjects, type)
                setObjectsType(p[3].afterObjects, type)

                leftSymbol.Code.extend(p[3].objects[idx])
                leftSymbol.StateType = 'equation'

                p[0].objects.append(p[1].objects[leftIdx])
                leftIdx+=1
    p[0].objects.extend(p[3].beforeObjects)
    p[0].objects.extend(p[3].afterObjects)
            #p[0].objects的内容为lex_value


def p_lhs(p):
    '''Lhs : LPARENTHESE RPARENTHESE
    | Lhs_id Lhs_1'''
    p[0] = lex_value("Lhs")
    if p[1].strs != 'lparenthese':
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)


def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | empty'''
    p[0] = lex_value("Lhs_1")
    if len(p) == 4:
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


# not finish
def p_lhs_id(p):
    '''Lhs_id : LV6ID'''
    p[0] = p[1]


# not finish
def p_user_op_decl_1(p):
    '''User_op_decl_1 : Size_decl
                      | empty'''
    p[0] = p[1]
    pass


def p_size_decl(p):
    '''Size_decl : LSHIFT Id_one_or_more_with_comma RSHIFT 
                 | LSHIFT RSHIFT'''
    p[0] = lex_value('Size_decl')


def p_user_op_decl_2(p):
    '''User_op_decl_2 : empty'''
    p[0] = p[1]
    pass


def p_user_op_decl_3(p):
    '''User_op_decl_3 : empty'''
    p[0] = p[1]
    pass


def p_in_params(p):
    'In_Params : Params'
    p[0] = p[1]
    for var in p[0].objects:
        symbol = thisEnv.getSymbolInThisEnv(var.value)
        symbol.IsInput = True


def p_out_params(p):
    'Out_Params : Params'
    p[0] = p[1]
    for var in p[0].objects:
        symbol = thisEnv.getSymbolInThisEnv(var.value)
        symbol.IsReturn = True


def p_params(p):
    'Params : LPARENTHESE Params_1 RPARENTHESE'
    p[0] = p[2]


def p_params_1(p):
    '''Params_1 : Var_decls Params_2
    | empty'''
    p[0] = lex_value('params_1')
    p[0].objects.extend(p[1].objects)
    if len(p) == 3:
        p[0].objects.extend(p[2].objects)


def p_params_2(p):
    '''Params_2 : SEMICOLON Var_decls Params_2
    | empty'''
    p[0] = lex_value('params_2')
    if len(p) == 4:
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
    # 直接将var_decls_2 var_decls_3 var_decls_4设置为空
    p[0] = lex_value('Var_decls')
    typeName = p[4].value
    if p[4].strs == "struct":
        # 此处生成的临时结构体，作用域应在根结点的符号表内
        tmpStructName = getName("tmpStruct")
        structSymbol = Symbol(tmpStructName, 'Type', 'struct')
        structSymbol.FieldList = objectsToStruct(p[4].objects)
        structSymbol.arrSize.extend(p[4].arrSize)
        rootSymbolTable = getRootSymbolTable(thisEnv)
        rootSymbolTable.setSymbol(tmpStructName, structSymbol)
        typeName = tmpStructName

    symbol = thisEnv.getSymbolInThisEnv(p[1].value)
    symbol.Type = typeName
    symbol.arrSize.extend(p[4].arrSize)
    if p[7].strs != 'Empty':
        symbol.Last.extend(p[7].objects)
    for i in range(len(p[2].objects)):
        symbol = thisEnv.getSymbolInThisEnv(p[2].objects[i].value)
        symbol.Type = typeName
        symbol.arrSize.extend(p[4].arrSize)
        if p[7].strs != 'Empty':
            symbol.Last.extend(p[7].objects)

    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)


def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
    p[0] = lex_value("var_decls_1")
    if len(p) == 4:
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
    p[0] = p[3]
    symbol = Symbol(p[3].value, 'Var', '')
    thisEnv.setSymbol(p[3].value, symbol)


def p_var_id_1(p):
    '''Var_id_1 : CLOCK
    | empty'''
    p[0] = p[1]


def p_var_id_2(p):
    '''Var_id_2 : PROBE
    | empty'''
    p[0] = p[1]


# not finish
def p_var_decls_2(p):
    'Var_decls_2 : empty'


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
    p[0] = p[1]


def p_last_decl(p):
    '''Last_decl : LAST EQU Expr'''
    p[0] = lex_value("Last_decl")
    p[0].objects.extend(p[3].objects)


def p_package(p):
    'Package : PACKAGE'
    global isPackage
    isPackage = 1
    p[0] = p[1]


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
    # Interface_status表示该变量是private or public 。是否是external
    external = True
    public = True
    if len(p[1].objects) == 1:
        external = False
    if p[1].objects[0].value == "private":
        public = False
    if p[4].strs == 'struct':  # 若为结构体，则是const imported c12:{tt1:bool,tt2:float32};
        # 创建一个变量，该symbol的Kind为type，结构体定义在kcg_types.h文件里
        type = getName('tmpStruct')
        typeSymbol = Symbol(type, "Type", 'struct')
        thisEnv.setSymbol(type, typeSymbol)
        typeSymbol.FieldList = objectsToStruct(p[4].objects)
    else:
        type = p[4].value
    if len(p) == 7:
        # 此处关于结构体的初始化还没有完成
        symbol = Symbol(p[2].value, 'Const', type, public, external, isPackage, packageName)
        symbol.arrSize.extend(p[4].objects)
        setObjectsType(p[6].objects[0], type)
        symbol.FieldList = objectsToStruct(p[4].objects)
        symbol.Code = p[6].objects[0]
        thisEnv.setSymbol(p[2].value, symbol)
    elif len(p) == 5:
        symbol = Symbol(p[2].value, 'Const', type, public, external, isPackage, packageName)
        symbol.arrSize.extend(p[4].objects)
        thisEnv.setSymbol(p[2].value, symbol)


def p_interface_status(p):
    '''Interface_status : Visibility_zero_or_one External
    | Visibility_zero_or_one'''
    p[0] = lex_value('Interface_status')
    if len(p) == 3:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
    elif len(p) == 2:
        p[0].objects.append(p[1])
    pass


def p_visibility_zero_or_one(p):
    '''Visibility_zero_or_one : Visibility
    | empty'''
    p[0] = p[1]


def p_external(p):
    'External : IMPORTED'
    # p[0]=lex_value('External')
    p[0] = p[1]


def p_visibility(p):
    '''Visibility : PRIVATE
    | PUBLIC'''
    p[0] = p[1]


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
        if p[3].strs == 'struct':
            typeName = getName("tmpStruct")
            typeSymbol = Symbol(typeName, "Type", 'struct')
            thisEnv.setSymbol(typeName, typeSymbol)
            typeSymbol.FieldList = objectsToStruct(p[3].objects)
        else:
            typeName = p[3].value
        symbol = Symbol(item.value, 'Sensor')
        symbol.Type = typeName
        thisEnv.setSymbol(item.value, symbol)
        symbol.arrSize.extend(p[3].objects)


def p_id_one_or_more_with_comma(p):
    'Id_one_or_more_with_comma : LV6ID Id_one_or_more_with_comma_1'
    p[0] = lex_value('Id_one_or_more_with_comma')
    p[0].objects.append(p[1])
    if len(p) == 3:
        p[0].objects.extend(p[2].objects)


def p_id_one_or_more_with_comma_1(p):
    '''Id_one_or_more_with_comma_1 : COMMA LV6ID Id_one_or_more_with_comma_1
    | empty'''
    p[0] = lex_value('Id_one_or_more_with_comma_1')
    if len(p) == 4:
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


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
    | LBPARENTHESE Field_decl Type_expr_1 RBPARENTHESE
    | Type_expr EXPONENT Expr'''
    # Type_expr_2表示是否是数组
    p[0] = lex_value('')
    if len(p) == 2:
        p[0].strs = p[1].strs
        p[0].value = p[1].value
        # if len(p[2].objects) != 0:
        #     p[0].objects.extend(p[2].objects)
    elif p[1].strs == 'signed' or p[1].strs == 'unsigned':
        # 没写完，需要将INTCONST改为Expr
        # 需要计算出Expr表达式代表的值，Expr可能是静态数组，结构体。
        # 该情况也可能出现数组，没有完成
        # num=exprToNum(p[3].objects)
        if p[1].strs == 'signed':
            type = "int" + str(p[3].value)
        elif p[1].strs == 'unsigned':
            type = "uint" + str(p[3].value)
        p[0].strs = type
        p[0].value = p[1].value
    elif p[1].strs == '{':
        # objects表示结构体的每个元素[[[lex_value("lv6id")],[type_expr]]]
        # arrSize指示其是否是数组
        p[0].strs = "struct"
        # p[0].objects.extend(p[5].objects)
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
    elif len(p)==4:
        p[0].strs=p[1].strs
        p[0].value=p[1].value
        if len(p[3].objects)!=0:
            p[0].arrSize.extend(p[3].objects)
        p[0].arrSize.extend(p[1].arrSize)
        p[0].objects.extend(p[1].objects)


def p_type_expr_1(p):
    '''Type_expr_1 : COMMA Field_decl Type_expr_1
    | empty'''
    if len(p) != 2:
        p[0] = lex_value("Type_expr_1")
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
    else:
        p[0] = p[1]


def p_field_decl(p):
    '''Field_decl : LV6ID COLON Type_expr'''
    p[0] = lex_value("Field_decl")
    field = list()
    field.append(p[1])
    if p[3].strs == "struct":
        tmpStructName = getName("tmpStruct")
        structSymbol = Symbol(tmpStructName, 'Type', 'struct')
        structSymbol.FieldList = objectsToStruct(p[3].objects)
        structSymbol.arrSize.extend(p[3].arrSize)
        rootSymbolTable = getRootSymbolTable(thisEnv)
        rootSymbolTable.setSymbol(tmpStructName, structSymbol)
        tmpLex_value = lex_value("struct", tmpStructName)
        tmpLex_value.objects.extend(p[3].objects)
        tmpLex_value.arrSize.extend(p[3].arrSize)
        field.append(tmpLex_value)
    else:
        field.append(p[3])
    p[0].objects.append(field)


def p_type_expr_2(p):
    '''Type_expr_2 : EXPONENT Expr Type_expr_2
    | empty'''
    p[0] = lex_value("Type_expr_2")
    if len(p) == 4:
        p[0].objects.append(p[2].objects[0])
        p[0].objects.extend(p[3].objects)


def p_path_1(p):
    '''Path_1 : DOUBLECOLON LV6ID Path_1
    | empty '''
    if len(p) != 2:
        p[0] = lex_value("Path_1")
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    else:
        p[0] = p[1]


def p_path_id(p):
    '''Path_id : LV6ID Path_1'''
    if p[2] != None and len(p[2].objects) != 0:
        symbol = Symbol()
        symbol.Code.append(p[1])
        symbol.Code.extend(p[2].objects[:-1])
        symbol.Name = symbol.changeName(thisEnv)
        # symbol.Kind = "PathId"
        symbol.isPathId=True
        thisEnv.setSymbol(symbol.Name, symbol) 
        p[0]=lex_value("Path_id",symbol.Name)
    else:
        tmpSymbol=thisEnv.getSymbolInThisEnv(p[1].value)
        if tmpSymbol==None:
            symbol=Symbol(p[1].value)
            thisEnv.setSymbol(p[1].value,symbol)
        p[0] = p[1]


def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    p[0] = lex_value("Id_expr")
    if len(p) == 2:
        p[0].objects.append(p[1])
    elif len(p) == 4:
        # if symbol !=None:
        #     p[0].objects.append(p[3])
        # else:
        realType = getIdType(p[3].value, thisEnv)
        lastName = getName("lastTmp")
        lastSymbol = Symbol(lastName, "TmpVar", realType.Type)
        thisEnv.setSymbol(lastName, lastSymbol)
        p[0].objects.append(lex_value("lv6id", lastName))
        lastSymbol.StateType = 'equation'
        lastSymbol.Code.append(p[3])
    elif len(p) == 3:
        pass


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
    | Apply_expr'''
    p[0] = lex_value("Expr")
    if p[1].strs != 'List_expr' and p[1].strs != 'Tempo_expr' and p[1].strs != 'Switch_expr':
        p[0].strs=p[1].strs
        p[0].objects = [p[1].objects]
    else:
        p[0].objects = p[1].objects
    p[0].beforeObjects = p[1].beforeObjects
    p[0].afterObjects = p[1].afterObjects


# arrow对应于C语言的三目运算符
# pre：需要在output中添加一个mem
def p_tempo_expr(p):
    '''Tempo_expr : Expr ARROW Expr
    | PRE Expr
    | FBY LPARENTHESE List SEMICOLON Expr SEMICOLON List RPARENTHESE'''
    # 若是init操作符，则需要向out结构体中添加init。若有重名，则使用init1（依此递增）
    symbol = thisEnv.getSymbolInThisEnv(op_kind_id)
    p[0] = lex_value("Tempo_expr")
    if len(p) == 4 and p[2].value == '->':
        if len(p[1].objects) != len(p[3].objects):
            raise NotImplementedError("tempo_expr arrow:error")

        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)

        for idx in range(len(p[1].objects)):
            initName = getName("init")
            initSymbol = Symbol(initName, "Init", "bool")
            initSymbol.IsReturn = True
            thisEnv.setSymbol(initName, initSymbol)
            # symbol.Returns.append(initName)

            initTmp = getName("initTmp")
            initLex = lex_value("lv6id", initTmp)
            initTmpSym = Symbol(initTmp, "TmpVar")
            initTmpSym.StateType = 'ifCondition'
            thisEnv.setSymbol(initTmp, initTmpSym)

            checkType(p[1], p[3], idx)
            rootNode=Node('ifCondition')
            rootNode.value.append(lex_value('lv6id',initName))
            leftNode=Node('equation')
            leftNode.value.extend(p[1].objects[idx])
            rightNode=Node('equation')
            rightNode.value.extend(p[3].objects[idx])
            rootNode.childNodeList.append(leftNode)
            rootNode.childNodeList.append(rightNode)

            initTmpSym.Code.append(rootNode)
            p[0].beforeObjects.append(initLex)

            p[0].objects.append([initLex])

        p[0].afterObjects.extend(p[1].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
        # for elem in p[0].beforeObjects:
        #     print("elem=",elem)
    elif len(p) == 3:
        # 若是pre操作符，需要向out添加mem_pre，用来存储上一个周期的值。若在符号表未找到，则无需添加mem_pre。
        # 则此时只需要输出上一个周期的值。可能出现pre(2)
        # expr可能是列表
        for idx in range(len(p[2].objects)):
            type = getTypefromObjects(p[2].objects[idx])
            preName = getName("mem_pre")
            # symbol.Returns.append(preName)
            preSymbol = Symbol(preName, "Pre", type)
            preSymbol.IsReturn = True
            preSymbol.StateType = 'equation'
            thisEnv.setSymbol(preName, preSymbol)

            tmpPreName = getName("tmp_pre")
            tmpPreSymbol = Symbol(tmpPreName, "TmpVar", type)
            tmpPreSymbol.Code.append(lex_value("lv6id", preName))
            tmpPreSymbol.StateType = 'equation'
            thisEnv.setSymbol(tmpPreName, tmpPreSymbol)

            p[0].objects.append([lex_value("lv6id", tmpPreName, "")])

            preSymbol.Code.extend(p[2].objects[idx])
            p[0].afterObjects.extend(p[2].afterObjects)
            p[0].afterObjects.append(lex_value("lv6id", preName, type))

        p[0].beforeObjects.extend(p[2].beforeObjects)
    elif len(p) == 9:
        # 若是fby操作符，首先在outC结构体中添加一个idx和数组
        # fby(input1;cycle;input2) cycle必须是静态表达式
        if len(p[3].objects) != len(p[7].objects):
            raise NotImplementedError("tempo_expr fby:error")

        p[0].beforeObjects += p[3].beforeObjects + p[5].beforeObjects + p[7].beforeObjects
        p[0].afterObjects += p[3].afterObjects + p[5].afterObjects + p[7].afterObjects
        for idx in range(len(p[3].objects)):
            initName = getName("init")
            initSymbol = Symbol(initName, "Init", "bool")
            initSymbol.IsReturn = True
            thisEnv.setSymbol(initName, initSymbol)
            # symbol.Returns.append(initName)

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
            # symbol.Returns.append(fbyIdx)
            # symbol.Returns.append(fbyArr)
            symbol.fbyList.append(fbyClass(fbyIdx, fbyArr))
            type = checkType(p[3], p[7], idx)
            fbyArrSymbol.Type = type

            fbyTmp = getName('fbyTmp')
            fbyTmpSymbol = Symbol(fbyTmp, "TmpVar", type)
            thisEnv.setSymbol(fbyTmp, fbyTmpSymbol)

            p[0].objects.append([lex_value('lv6id', fbyTmp)])

            fbyTmpSymbol.StateType = 'fbyBlock'
            fbyTmpSymbol.Code.append([lex_value('lv6id', initName)])
            fbyTmpSymbol.Code.append([lex_value('lv6id', fbyIdx)])
            fbyTmpSymbol.Code.append([lex_value('lv6id', fbyArr)])
            fbyTmpSymbol.Code.append(p[3].objects[idx])
            fbyTmpSymbol.Code.append(p[5].objects[0])
            fbyTmpSymbol.Code.append(p[7].objects[idx])

            p[0].beforeObjects.append(lex_value('lv6id', fbyTmp))


def p_relation_expr(p):
    '''Relation_expr : Expr EQU Expr
    | Expr NOEQU Expr
    | Expr LESS Expr
    | Expr GREATER Expr
    | Expr LESSEQU Expr
    | Expr GREATEREQU Expr'''

    p[0] = lex_value("Relation_expr")
    if p[2].strs == '<>':
        p[2].value = '!='
    elif p[2].strs == '=':
        p[2].value = '=='
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].beforeObjects.extend(p[3].beforeObjects)

    if len(p[1].objects) != len(p[3].objects) and len(p[1].objects) != 1:
        raise NotImplementedError("relation_epxr:error")
    checkType(p[1], p[3], 0)
    p[0].objects.append(lex_value("", "("))
    p[0].objects.extend(p[1].objects[0])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects[0])
    p[0].objects.append(lex_value("", ")"))

    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].afterObjects.extend(p[3].afterObjects)


def judgeIsEnum(objects):
    symName = ""
    for elem in objects:
        if elem.strs == 'lv6id':
            symbol = thisEnv.getSymbolInThisEnv(elem.value)
            if symbol != None:
                value = symbol.Type
                while value not in typeArr:  # 存在该变量的类型是重命名之后，因此需要找到该变量的最初类型
                    symbol = thisEnv.getSymbolInThisEnv(value)
                    value = symbol.Type
                symName = symbol.Name
    return symName


def checkEnum(eName, objects):
    isUnderline = False
    sum = 0
    eSymbol = thisEnv.getSymbolInThisEnv(eName)
    eDict = dict()
    for elem in eSymbol.Code:
        eDict[elem.value] = 1
    for elem in objects:
        if elem[0][0].strs == '_':
            isUnderline = True
        elif elem[0][0].strs == 'enum_lv6id':
            eDict[elem[0][0].value] -= 1
    for key, value in eDict.items():
        if value == 1:
            sum += 1
    if (sum >= 1 and isUnderline == True) or (sum == 0 and isUnderline == False):
        return True
    return False


# 往符号表添加一个局部变量存储if表达式的结果。if (boolExpr){ localVar=Expr1;}else{ localVar=Expr2;}
def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr
    | LPARENTHESE CASE Expr OF Switch_expr_1 RPARENTHESE'''
    p[0] = lex_value("Switch_expr")
    if p[1].value == 'if':
        if len(p[4].objects) != len(p[6].objects):
            raise NotImplementedError("switch_expr if error")
        p[0].beforeObjects += p[2].beforeObjects + p[4].beforeObjects + p[6].beforeObjects
        for idx in range(len(p[4].objects)):
            ifTmp = getName("ifTmp")
            ifSymbol = Symbol(ifTmp, "TmpVar")
            ifSymbol.StateType = 'ifCondition'
            thisEnv.setSymbol(ifTmp, ifSymbol)

            rootNode=Node('ifCondition')
            rootNode.value.extend(p[2].objects[0])
            leftNode=Node('equation')
            leftNode.value.extend(p[4].objects[idx])
            rightNode=Node('equation')
            rightNode.value.extend(p[6].objects[idx])
            rootNode.childNodeList.append(leftNode)
            rootNode.childNodeList.append(rightNode)
            ifSymbol.Code.append(rootNode)

            p[0].beforeObjects.append(lex_value("lv6id", ifTmp))

            p[0].objects.append([lex_value("lv6id", ifTmp)])

        p[0].afterObjects += p[2].afterObjects + p[4].afterObjects + p[6].afterObjects
    else:
        symName = judgeIsEnum(p[3].objects[0])
        exprSymbol = thisEnv.getSymbolInThisEnv(symName)
        if exprSymbol == None:
            raise NotImplementedError("Switch_expr Error")
        if exprSymbol.Type == "enum":
            if checkEnum(exprSymbol.Name, p[5].objects[0]) == False:
                raise NotImplementedError("Switch_expr enum Error")
        conditionNode=Node('switchCondition')
        conditionNode.value.extend(p[3].objects[0])
        for idx in range(len(p[5].objects)):
            caseName = getName("caseTmp")
            caseSymbol = Symbol(caseName, "TmpVar")
            caseSymbol.StateType = 'switchCondition'
            caseSymbol.Code.append(conditionNode)
            thisEnv.setSymbol(caseName, caseSymbol)

            for elem in p[5].objects[idx]:
                switchNode=Node('equation')
                switchNode.pattern.extend(elem[0])
                switchNode.value.extend(elem[1])
                conditionNode.childNodeList.append(switchNode)

            p[0].beforeObjects.append(lex_value('lv6id', caseName))
            p[0].objects.append([lex_value("lv6id", caseName)])


def p_switch_expr_1(p):
    'Switch_expr_1 : Case_expr Switch_expr_2'
    p[0] = lex_value('Switch_expr_1')
    for idx in range(len(p[1].objects)):
        p[0].objects.append([p[1].objects[idx]])
    for idx in range(len(p[2].objects)):
        p[0].objects[idx].extend(p[2].objects[idx])


def p_switch_expr_2(p):
    '''Switch_expr_2 : Case_expr Switch_expr_2
    | empty'''
    p[0] = lex_value("Switch_expr_2")
    if len(p) == 3:
        for idx in range(len(p[1].objects)):
            p[0].objects.append([p[1].objects[idx]])
        for idx in range(len(p[2].objects)):
            p[0].objects[idx].extend(p[2].objects[idx])


def p_case_expr(p):
    'Case_expr : VERTICALBAR Pattern COLON Expr'
    p[0] = lex_value('Case_expr')
    for idx in range(len(p[4].objects)):
        tmpList = list()
        tmpList.append([p[2]])
        tmpList.append(p[4].objects[idx])
        p[0].objects.append(tmpList)


def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | Pattern_1 INTEGERNUM
    | Bool_atom
    | UNDERLINE'''
    if len(p) == 3:
        p[0] = p[2]
        p[2].value = str(-p[2].value)
    else:
        p[0] = p[1]
        if p[0].strs == 'lv6id':
            p[0].strs = 'enum_lv6id'


def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
    p[0] = p[1]


def p_arith_expr(p):
    '''Arith_expr : LPARENTHESE Expr COLON Type_expr RPARENTHESE'''
    p[0] = lex_value("Arith_expr")
    realType = p[4].value
    if realType not in typeArr:
        realType = getIdType(p[4].value, getRootSymbolTable(thisEnv)).Type
    p[0].objects.append(lex_value("", "(kcg_%s)" % (realType)))
    if len(p[2].objects[0]) != 1:
        p[0].objects.append(lex_value("", "("))
    setObjectsType(p[2].objects[0], realType)
    p[0].objects.extend(p[2].objects[0])

    if len(p[2].objects[0]) != 1:
        p[0].objects.append(lex_value("", ")"))


def p_arith_expr_unary(p):
    '''Arith_expr : MINUS Expr %prec UMINUS
    | PLUS Expr %prec UPLUS
    | LNOT Expr'''
    p[0] = lex_value("Arith_expr")
    p[0].beforeObjects.extend(p[2].beforeObjects)
    type = getTypefromObjects(p[2].objects[0])
    setObjectsType(p[2].objects[0], type)
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
    checkType(p[1], p[3], 0)
    if p[2].strs == 'mod':
        p[2].value = ' % '
    elif p[2].strs == 'land':
        p[2].value = ' & '
    elif p[2].strs == 'lor':
        p[2].value = ' | '
    elif p[2].strs == 'lxor':
        p[2].value = ' ^ '
    elif p[2].strs == 'lsl':
        p[2].value = ' << '
    elif p[2].strs == 'lsr':
        p[2].value = ' >> '
    p[0].objects.append(lex_value("", "("))
    p[0].objects.extend(p[1].objects[0])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects[0])
    p[0].objects.append(lex_value("", ")"))
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].beforeObjects.extend(p[3].beforeObjects)
    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].afterObjects.extend(p[3].afterObjects)

def p_apply_expr(p):
    '''Apply_expr : Operator LPARENTHESE List RPARENTHESE'''
    p[0] = lex_value("Apply_expr")
    applySymbol=thisEnv.getSymbolInThisEnv(p[1].value)
    applySymbol.StateType="ApplyExpr"
    for obj in p[3].objects:
        applySymbol.Params.append(obj[0])
    p[1].type="ApplyExpr"
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects[0])
    p[0].objects.append(p[4])
    # calledOperators.append(p[1].value) # p[1].value应该是Operator的名称
    # print("thisEnv.PrevTable",thisEnv.PrevTable.EnvName)
    thisEnv.PrevTable.getSymbolInThisEnv(p[1].value).isCalled=True
    globalSymbol=thisEnv.PrevTable.getSymbolInThisEnv(op_kind_id)
    globalSymbol.callOperators.append(p[1].value)

    
# not finish
def p_prefix(p):
    '''Prefix : Path_id'''
    p[0] = p[1]

# not finish
def p_operator(p):
    '''Operator : Prefix'''
    p[0] = p[1]


def p_list_expr(p):
    '''List_expr : LPARENTHESE List RPARENTHESE'''
    p[0] = lex_value("List_expr")
    p[0].objects.extend(p[2].objects)
    p[0].beforeObjects.extend(p[2].beforeObjects)
    p[0].afterObjects.extend(p[2].afterObjects)


def p_list(p):
    '''List : List_1
    | empty'''
    p[0] = lex_value("List")
    if p[1].strs == "List_1":
        p[0].objects.extend(p[1].objects)
        p[0].beforeObjects.extend(p[1].beforeObjects)
        p[0].afterObjects.extend(p[1].afterObjects)


def p_list_1(p):
    '''List_1 : Expr List_2'''
    p[0] = lex_value("List_1")
    p[0].objects.extend(p[1].objects)
    p[0].beforeObjects.extend(p[1].beforeObjects)
    p[0].afterObjects.extend(p[1].afterObjects)
    p[0].objects.extend(p[2].objects)
    p[0].beforeObjects.extend(p[2].beforeObjects)
    p[0].afterObjects.extend(p[2].afterObjects)


def p_list_2(p):
    '''List_2 : COMMA Expr List_2
    | empty'''
    p[0] = lex_value("List_2")
    if len(p) == 4:
        p[0].objects.extend(p[2].objects)
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].objects.extend(p[3].objects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[3].afterObjects)


# typed_integer和typed_float未添加
def p_atom(p):
    '''Atom : Bool_atom
    | INTEGERNUM
    | FLOATNUM
    | CHARACTER'''
    p[0] = lex_value("Atom")
    p[0].objects.append(p[1])


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    p[0] = p[1]


def p_bool_expr(p):
    '''Bool_expr : NOT Expr
    | HASHTAG LPARENTHESE List RPARENTHESE'''
    p[0] = lex_value("Bool_expr")
    if len(p) == 3:
        p[1].value = '!'
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects[0])
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
    elif len(p) == 5:
        for idx in range(len(p[3].objects)):
            p[0].objects.append(lex_value("", "("))
            p[0].objects.extend(p[3].objects[idx])
            p[0].objects.append(lex_value("", ")"))
            if idx != len(p[3].objects) - 1:
                p[0].objects.append(lex_value("", "+"))
        p[0].objects.append(lex_value("", "<=1"))


def p_bool_expr_bin(p):
    '''Bool_expr : Expr AND Expr
    | Expr OR Expr
    | Expr XOR Expr'''
    p[0] = lex_value('Bool_expr')
    if p[2].strs == 'and':
        p[2].value = ' & '
    elif p[2].strs == 'or':
        p[2].value = ' | '
    elif p[2].strs == 'xor':
        p[2].value = ' ^ '
    p[0].objects.append(lex_value("", "("))
    p[0].objects += p[1].objects[0]
    p[0].objects.append(p[2])
    p[0].objects += p[3].objects[0]
    p[0].objects.append(lex_value("", ")"))
    p[0].beforeObjects += p[1].beforeObjects + p[3].beforeObjects
    p[0].afterObjects += p[1].afterObjects + p[3].afterObjects


def p_struct_expr(p):
    '''Struct_expr : Expr POINT LV6ID
    | LBPARENTHESE Label_expr Struct_expr_1 RBPARENTHESE'''
    p[0] = lex_value("Struct_expr")
    if len(p) == 5:
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
    elif len(p) == 4:
        idx1 = len(p[1].objects) - 1
        idx2 = len(p[1].objects[idx1]) - 1
        p[1].objects[idx1][idx2].objects.append(p[3])
        p[0].objects.extend(p[1].objects[0])
        # print("Struct_expr",p[1].objects,type(p[1].objects[0][0]))


def p_struct_expr_1(p):
    '''Struct_expr_1 : COMMA Label_expr Struct_expr_1
    | empty'''
    p[0] = lex_value("Struct_expr_1")
    if len(p) != 2:
        p[0].beforeObjects.extend(p[2].beforeObjects)
        p[0].beforeObjects.extend(p[3].beforeObjects)
        p[0].afterObjects.extend(p[2].afterObjects)
        p[0].afterObjects.extend(p[3].afterObjects)
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


def p_label_expr(p):
    '''Label_expr : LV6ID COLON Expr'''
    p[0] = lex_value("Label_expr")
    p[0].beforeObjects.extend(p[3].beforeObjects)
    p[0].afterObjects.extend(p[3].afterObjects)
    labelList = list()
    labelList.append(p[1])
    labelList.extend(p[3].objects)
    p[0].objects.append(labelList)

def p_array_expr(p):
    '''Array_expr : LBRACKET List RBRACKET
    | Expr Index'''
    p[0]=lex_value("Array_expr")
    if len(p)==4:
        print("array_expr",p[2].objects)
        p[0].strs='Array_list_expr'
        p[0].objects.extend(p[2].objects)
    else:
        p[1].objects[0][len(p[1].objects[0])-1].arrSize.extend(p[2].objects)
        p[0].objects.extend(p[1].objects[0])

def p_array_expr2(p):
    '''Array_expr : REVERSE Expr
    | Expr AT Expr'''
    if len(p)==3:
        pass
    else:
        pass

def p_array_expr3(p):
    '''Array_expr : Expr EXPONENT Expr
    | Expr LBRACKET Expr TPOINT Expr RBRACKET'''
    pass

def p_array_expr4(p):
    '''Array_expr : LPARENTHESE Expr POINT Array_expr_1 DEFAULT Expr RPARENTHESE
    | TRANSPOSE LPARENTHESE Expr SEMICOLON INTEGERNUM SEMICOLON INTEGERNUM RPARENTHESE'''
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

def p_index(p):
    '''Index : LBRACKET Expr RBRACKET'''
    p[0]=lex_value("Index")
    p[0].objects.append(p[1])
    setObjectsType(p[2].objects[0],"int8")
    p[0].objects.extend(p[2].objects[0])
    p[0].objects.append(p[3])

def p_array_expr2(p):
    '''Array_expr : REVERSE Expr'''
    pass

def p_error(p):
    print("Syntax error in input!")


def p_empty(p):
    'empty :'
    p[0] = lex_value('Empty')


def get_parse(strs):
    global program
    parser = yacc(debug=1)
    parse = yacc(debug=1)
    pattern = r'\#[\w]+'
    strs = re.sub(pattern, '', strs)
    print("=======strs=====\n", strs)
    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)
    return program, GlobalEnv




if __name__ == '__main__':
    parser = yacc(debug=1)
    strs = '''
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
    returns o; '''

    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)
    print(nodes)
