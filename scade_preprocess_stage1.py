import copy
from ply.yacc import yacc
from scade_lex import *
from SymbolClass import *
import re
import argparse
import os

class graphTree:
    def __init__(self,Name = "",Type= ""):
        self.name = Name
        self.preNode=None
        self.type = Type #root,package,node,applyFunc
        self.son=list()
    
def traversal(graphTree,path,strList):
    if graphTree.name != "" and graphTree.type != 'applyFunc':
        path.append(graphTree.name)
    if graphTree.type == 'applyFunc':
        tmpstr="\""+'::'.join(path)+"\""
        tmpstr+="-> \"%s\";"%(graphTree.name)
        strList.add(tmpstr)
        return
    else:
        for elem in graphTree.son:
            traversal(elem,path,strList)
        if len(path)!=0:
            path.pop()
    
def lexObjectsToString(objects):
    tmpstr=""
    for obj in objects:
        if not isinstance(obj.value,str):
            tmpstr+=str(obj.value)
        else:
            tmpstr+=obj.value
        if obj.value == ';' or obj.value =='let' or obj.value=='tel' :
            tmpstr+="\n"
        else:
            tmpstr+=" "
    return tmpstr

def writeFile(node):
    path=list()
    strList=set()    
    traversal(node,path,strList)
    tmpstr="digraph{\n"
    for elem in strList:
        tmpstr+="%s\n"%elem
    tmpstr+="}"
    file=open("test_aircraft_brake_system.dot",'w')
    file.write(tmpstr)
    # print("======dot file=====\n")
    # print(tmpstr)

def getName(name,symtable):
    for index in range(100):
        tmp_name=f"{name}_{index}"
        if symtable.getSymbolInThisEnv(tmp_name) == None:
            return tmp_name


programNode=graphTree("","root")
curNode=programNode
rootSymtable=SymbolTable('Global')
rootSymbol=Symbol('Global')
curSymtable=rootSymtable
scade_lexer=scade_lex()

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

class topologyNode:
    def __init__(self,name='',index=0,tpIdx=0,inNum=0):
        self.name=name
        self.index=index
        self.tpIdx=tpIdx
        self.inNum=inNum
        self.finish=False
    def __repr__(self): 
        return f'name:{self.name} index:{self.index} inNum:{self.inNum}\n'

def topologySort(symbolList,adjList,nodeList):
    sum=len(nodeList)
    retList=[]
    for i in range(sum):
        if len(retList)>=sum:
            break
        for elem in nodeList:
            if len(retList)>=sum:
                break
            if elem.inNum==0 and elem.finish==False:
                retList.append(symbolList[elem.tpIdx])
                elem.finish=True
                for j in range(len(adjList[elem.index])):
                    idx=adjList[elem.index][j]
                    nodeList[idx].inNum-=1
    return retList


# def topologyReady(symbolList):
#     adjList=[]
#     nodeDict={}
#     nodeList=[]
#     num=0
#     for idx in range(0,len(symbolList)):
#         leftName=symbolList[idx].Name
#         if leftName not in nodeDict.keys():
#             node=topologyNode(leftName,num,idx)
#             nodeList.append(node)
#             nodeDict[leftName]=num
#             num+=1
#             adjList.append([])
#         else:
#             raise NotImplementedError('%s redefined'%leftName)
#     for elem in symbolList:
#         adjIdx1=nodeDict[elem.Name]
#         for relyElem in elem.relyList:
#             if relyElem in nodeDict.keys():
#                 adjIdx2=nodeDict[relyElem]
#                 nodeList[adjIdx1].inNum+=1
#                 nodeList[adjIdx2].outNum+=1
#                 adjList[adjIdx2].append(adjIdx1)
#     return topologySort(symbolList,adjList,nodeList)

def getWholePathFromTopToDown(pathList,idx,symtable):
    if idx>=len(pathList):
        return True
    if symtable.getSymbolInThisEnv(pathList[idx])!=None:
        for elem in symtable.ChildTableList:
            if elem.EnvName==pathList[idx]:
                return getWholePathFromTopToDown(pathList,idx+1,elem)
        return True
    # print("==None",symtable.EnvName)
    return False

def getSameLevelRely(symtable):
    print("getSameLevelRely symtable.EnvName:",symtable.EnvName)
    global rootSymtable
    nodeList=[]
    nodeIdxDict={}
    adjList=[]
    symbolList=[]
    num=0
    for _,symbol in symtable.SymbolTable.items():
        if symbol.Kind=='OpKind' or symbol.Kind=='Package':
            tpNode=topologyNode(symbol.Name,num,num)
            nodeList.append(tpNode)
            nodeIdxDict[symbol.Name]=num
            symbolList.append(symbol)
            num+=1
            adjList.append([])
    for _,symbol in symtable.SymbolTable.items():
        if symbol.Kind =='OpKind' or symbol.Kind=='Package':
            print("getSameLevelRely symbol.Name=",symbol.Name," relyList=",symbol.relyList,symbol.Kind)
            for idx,elem in enumerate(symbol.relyList):
                pathList=elem.split("::")
                ret=getWholePathFromTopToDown(pathList,0,rootSymtable)
                if ret==False:
                    ret=getWholePathFromTopToDown(pathList,0,symtable)
                    if symtable.EnvName == 'Global':
                        curPath=[]
                    else:
                        curPath=symtable.PrevTable.getSymbolInThisEnv(symtable.EnvName).PackageName.split('::')
                    pathList=curPath+pathList
                    if ret==True:
                        symbol.relyList[idx] ='::'.join(pathList)
                    else:
                        raise NotImplementedError("Path error",pathList)
            global rootSymbol
            fSymbol=rootSymbol
            if symtable.EnvName!='Global':
                fSymbol=symtable.PrevTable.getSymbolInThisEnv(symtable.EnvName)
            fname=fSymbol.PackageName
            #在此处进行拓扑排序
            symbol.relyList=list(set(symbol.relyList))
            print("symbol.Name",symbol.Name,symbol.relyList)
            for relyElem in symbol.relyList:
                if len(relyElem)>len(fname) and relyElem[:len(fname)]==fname:
                    relyName=relyElem
                    if len(fname)!=0:
                        relyName=relyElem[len(fname)+2:]
                    idx=relyName.find("::")
                    if idx!=-1:
                        relyName=relyName[:idx]
                    if symtable.SymbolTable[relyName]!=None and (symtable.SymbolTable[relyName].Kind=='OpKind' or symtable.SymbolTable[relyName].Kind=='Package'):
                        idx1=nodeIdxDict[symbol.Name]
                        idx2=nodeIdxDict[relyName]
                        nodeList[idx1].inNum+=1
                        adjList[idx2].append(idx1)
                else:
                    fSymbol.relyList.append(relyElem)
    retList=topologySort(symbolList,adjList,nodeList)
    return retList

def ReOrder(symtable): 
    for symbolName,symbol in symtable.SymbolTable.items():
        if symbol.Kind=='Package':
             for childTable in symtable.ChildTableList:
                 if childTable.EnvName==symbolName:
                    ReOrder(childTable)
    global rootSymbol
    packageSymbol=rootSymbol
    if symtable.EnvName != 'Global':
        packageSymbol=symtable.PrevTable.SymbolTable[symtable.EnvName]
    retList=getSameLevelRely(symtable)
    # print("packageSymbol=",packageSymbol.Name)
    # if symtable.EnvName!='Global':
    #     str="package "+symtable.EnvName
    #     packageSymbol.Code.append(str)
    for elem in retList:
        packageSymbol.Code+=symtable.SymbolTable[elem.Name].Code
    if symtable.EnvName!='Global':
        str="end;\n"
        packageSymbol.Code.append(str)

def p_program(p):
    'Program : Decls_zero_or_more'
    p[0]=lex_value("Program")
    p[0].objects.extend(p[1].objects)
    ReOrder(curSymtable)


def p_decls_zero_or_more(p):
    '''Decls_zero_or_more : Decls Decls_zero_or_more
    | empty'''
    p[0]=lex_value("Decls_zero_or_more")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)
        # tmpstr = p[1].Code[0]
        # if len(p[2].Code)!=0:
        #     tmpstr+=p[2].Code[0]
        # p[0].Code.append(tmpstr)


def p_decls(p):
    '''Decls : Const_block
    | Type_block
    | Sensor_block
    | Package_decl
    | User_op_decl
    | Group_block
    | OPEN Path_id SEMICOLON'''
    #TODO:group_block和open path 
    p[0]=lex_value("Decls")
    if len(p)!=3:
        p[0].objects.extend(p[1].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        # p[0].objects.extend(p[2].objects)
    # if len(p)==3:
    #     tmpstr=lexObjectsToString(p[1].objects)
    #     p[0].Code.append(tmpstr)
    # else:
    #     tmpstr = p[1].value + lexObjectsToString(p[2].objects)
    #     p[0].Code.append(tmpstr)


def p_group_block(p):
    '''Group_block : GROUP Group_block_1'''
    p[0]=lex_value("Group_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_group_block_1(p):
    '''Group_block_1 : Group_decl SEMICOLON Group_block_1
                     | empty'''
    p[0]=lex_value("Group_block_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)

def p_group_decl(p):
    '''Group_decl : Visibility_zero_or_one LV6ID EQU Group_expr'''
    p[0]=lex_value("Group_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)

def p_group_expr(p):
    '''Group_expr : LPARENTHESE Type_expr Group_expr_1 RPARENTHESE'''
    p[0]=lex_value("Group_expr")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)
    p[0].objects.append(p[4])

def p_group_expr_1(p):
    '''Group_expr_1 : COMMA Type_expr Group_expr_1
                    | empty'''
    p[0]=lex_value("Group_expr_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


def p_type_block(p):
    'Type_block : TYPE Type_block_1'
    p[0]=lex_value("Type_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    if curSymtable.EnvName=='Global':
        global rootSymbol
        rootSymbol.Code.append(lexObjectsToString(p[0].objects))
    else:
        packageSymbol=curSymtable.PrevTable.getSymbolInThisEnv(curSymtable.EnvName)
        packageSymbol.Code.append(lexObjectsToString(p[0].objects))
    


def p_type_block_1(p):
    '''Type_block_1 : Type_decl SEMICOLON Type_block_1
                    | empty'''
    p[0]=lex_value("Type_block_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


def p_Type_decl(p):
    'Type_decl : Interface_status LV6ID Type_decl_1 Type_decl_2'
    p[0]=lex_value("Type_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)
    p[0].objects.extend(p[4].objects)
    global curSymtable
    symbol = Symbol(p[2].value,'Type')
    curSymtable.setSymbol(p[2].value,symbol)


def p_Type_decl_1(p):
    '''Type_decl_1 : EQU Type_def
                    | empty'''
    p[0]=lex_value("Type_decl_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)


def p_type_decl_2(p):
    '''Type_decl_2 : IS Numeric_kind
                   | empty'''
    p[0]=lex_value("Type_decl_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)


def p_type_def(p):
    '''Type_def : Type_expr
                | ENUM LBPARENTHESE Id_one_or_more_with_comma RBPARENTHESE'''
    p[0]=lex_value("Type_def")
    if len(p)==2:
        p[0].objects.extend(p[1].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])


def p_numeric_kind(p):
    '''Numeric_kind : NUMERIC
    | FLOAT
    | INTEGER
    | SIGNED
    | UNSIGNED'''
    p[0]=lex_value("Numeric_kind")
    p[0].objects.append(p[1])


def p_package_decl(p):
    'Package_decl : Package Visibility_zero_or_one Pack_Lv6id Decls_zero_or_more END SEMICOLON'
    global curNode
    curNode=curNode.pre
    p[0]=lex_value("Package_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)
    p[0].objects.extend(p[4].objects)
    p[0].objects.append(p[5])
    p[0].objects.append(p[6])
    # tmpstr = lexObjectsToString(p[1].objects) + lexObjectsToString(p[2].objects) + lexObjectsToString(p[3].objects)
    # if len(p[4].Code)!=0:
    #     tmpstr+=p[4].Code[0]
    # tmpstr += p[5].value + p[6].value
    # p[0].Code.append(tmpstr)

    global curSymtable
    curSymtable=curSymtable.PrevTable

def p_user_op_decl(p):
    'User_op_decl : Op_kind Interface_status User_op_decl_Lv6id User_op_decl_1 In_Params RETURNS Out_Params User_op_decl_2 User_op_decl_3 Opt_body'
    global curNode
    curNode=curNode.pre
    p[0]=lex_value("User_op_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)
    p[0].objects.extend(p[4].objects)
    p[0].objects.extend(p[5].objects)
    p[0].objects.append(p[6])
    p[0].objects.extend(p[7].objects)
    p[0].objects.extend(p[8].objects)
    p[0].objects.extend(p[9].objects)
    p[0].objects.extend(p[10].objects)

    global curSymtable
    curSymtable=curSymtable.PrevTable
    symbol=curSymtable.getSymbolInThisEnv(p[3].objects[0].value)
    tmpstr=lexObjectsToString(p[0].objects)
    symbol.Code.append(tmpstr)
    print("=====Node:",p[3].objects[0].value," relyList======")
    print(symbol.relyList)
    print(tmpstr)
    print("======")
    # p[0].Code.append(tmpstr)


def p_pack_lv6id(p):
    'Pack_Lv6id : LV6ID'
    p[0]=lex_value("Pack_Lv6id")
    p[0].objects.append(p[1])

    global curSymtable
    symTable=SymbolTable(p[1].value)
    curSymtable.ChildTableList.append(symTable)
    symTable.PrevTable=curSymtable

    symbol=Symbol(p[1].value,"Package")
    curSymtable.setSymbol(p[1].value,symbol)
    symbol.Code.append("package %s\n"%p[1].value)
    if curSymtable.EnvName=='Global':
        symbol.PackageName=p[1].value
    else:
        symbol.PackageName="%s::%s"%(curSymtable.PrevTable.getSymbolInThisEnv(curSymtable.EnvName).PackageName,p[1].value)

    curSymtable=symTable

    global curNode
    node=graphTree(p[1].value,"package")
    node.pre=curNode
    curNode.son.append(node)
    curNode=node
    print("this package is ",p[1].value)


def p_user_op_decl_Lv6id(p):
    'User_op_decl_Lv6id : LV6ID'
    p[0]=lex_value("User_op_decl_Lv6id")
    p[0].objects.append(p[1])

    global curSymtable
    symTable=SymbolTable(p[1].value)
    curSymtable.ChildTableList.append(symTable)
    symTable.PrevTable=curSymtable

    symbol=Symbol(p[1].value,'OpKind')
    if curSymtable.EnvName=='Global':
        symbol.PackageName=p[1].value
    else:
        symbol.PackageName='%s::%s'%(curSymtable.PrevTable.getSymbolInThisEnv(curSymtable.EnvName).PackageName,p[1].value)
    curSymtable.setSymbol(p[1].value,symbol)

    curSymtable=symTable

    global curNode
    node=graphTree(p[1].value,"node")
    node.pre=curNode
    curNode.son.append(node)
    curNode=node
    print("this node is ",p[1].value)


def p_state_lv6id(p):
    'State_Lv6id : LV6ID'
    p[0]=p[1]


def p_op_kind(p):
    '''Op_kind : FUNCTION
    | NODE'''
    p[0]=lex_value("Op_kind")
    p[0].objects.append(p[1])

#Equation_zero_or_more_with_semicolon在此处需要拓扑排序
def p_opt_body(p):
    '''Opt_body : SEMICOLON
    | Equation SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL SEMICOLON
    | Signal_block_zero_or_one Local_block_zero_or_one LET Equation_zero_or_more_with_semicolon TEL'''
    p[0]=lex_value("Opt_body")
    if len(p)==2:
        p[0].objects.append(p[1])
    elif len(p)==3:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
    else:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)
        p[0].objects.append(p[3])
        p[0].objects.extend(p[4].objects)
        p[0].objects.append(p[5])
        if len(p)==7:
            p[0].objects.append(p[6])


def p_signal_block_zero_or_one(p):
    '''Signal_block_zero_or_one : Signal_block
    | empty'''
    p[0]=lex_value("Signal_block_zero_or_one")
    if p[1].strs=='Signal_block':
        p[0].objects.extend(p[1].objects)

def p_signal_block(p):
    'Signal_block : SIG Id_one_or_more_with_comma SEMICOLON'
    p[0]=lex_value("Signal_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])

def p_local_block_zero_or_one(p):
    '''Local_block_zero_or_one : Local_block
    | empty'''
    p[0]=lex_value("Local_block_zero_or_one")
    if p[1].strs=='Local_block':
        p[0].objects.extend(p[1].objects)


def p_local_block(p):
    '''Local_block : VAR Local_block_1
    | empty'''
    p[0]=lex_value("Local_block")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)


def p_local_block_1(p):
    '''Local_block_1 : Var_decls SEMICOLON Local_block_1
    | empty'''
    p[0]=lex_value("Local_block_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    

def p_equation_zero_or_more_with_semicolon(p):
    '''Equation_zero_or_more_with_semicolon : Equation SEMICOLON Equation_zero_or_more_with_semicolon
    | empty'''
    p[0]=lex_value("Equation_zero_or_more_with_semicolon")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


def p_equation(p):
    '''Equation : Simple_equation
                | Assert
                | Control_block Return
                | Emission'''
    #TODO:Emission未完成
    p[0]=lex_value("Equation")
    p[0].objects.extend(p[1].objects)
    if len(p)==3:
        p[0].objects.extend(p[2].objects)

def p_emission(p):
    '''Emission : EMIT Emission_body'''
    #TODO:not finish
    p[0]=lex_value("Emission")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_emission_body(p):
    '''Emission_body : SINGLEQUOTE LV6ID Emission_body_1
                    | LPARENTHESE SINGLEQUOTE LV6ID Emission_body_2 RPARENTHESE Emission_body_1'''
    #TODO:not finish
    p[0]=lex_value("Emission_body")
    if len(p)==4:
        # p[0].objects.append(p[1])
        p[2].value = p[1].value + p[2].value
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    else:
        p[0].objects.append(p[1])
        # p[0].objects.append(p[2])
        p[3].value = p[2].value + p[3].value
        p[0].objects.append(p[3])
        p[0].objects.extend(p[4].objects)
        p[0].objects.append(p[5])
        p[0].objects.extend(p[6].objects)

def p_emission_body_1(p):
    '''Emission_body_1 : IF Expr
                        | empty'''
    #TODO:not finish
    p[0]=lex_value("Emission_body_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)

def p_emission_body_2(p):
    '''Emission_body_2 : COMMA SINGLEQUOTE Emission_body_2
                        | empty'''
    p[0]=lex_value("Emission_body_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)

def p_assert(p):
    '''Assert : ASSUME LV6ID COLON Expr
            | GUARANTEE LV6ID COLON Expr'''
    p[0]=lex_value("Assert")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)


def p_control_block(p):
    '''Control_block : State_machine
    | Clocked_block'''
    p[0]=lex_value("Control_block")
    p[0].objects.extend(p[1].objects)


def p_return(p):
    '''Return : RETURNS Returns_var'''
    p[0] = lex_value("Return")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_returns_var(p):
    '''Returns_var : Returns_var_1 Returns_var_2'''
    p[0]=lex_value("Returns_var")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)


def p_returns_var_1(p):
    '''Returns_var_1 : Returns_var_1 LV6ID COMMA
    | empty'''
    p[0]=lex_value("Returns_var_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend([p[2],p[3]])

def p_returns_var_2(p):
    '''Returns_var_2 : LV6ID
    | TPOINT'''
    p[0]=lex_value("Returns_var_2")
    p[0].objects.append(p[1])

def p_state_machine(p):
    '''State_machine : AUTOMATON Id_zero_or_one State_machine_1'''
    p[0]=lex_value("State_machine")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)

    global curSymtable
    curSymtable=curSymtable.PrevTable

def p_state_machine_1(p):
    '''State_machine_1 : State_decl State_machine_1
                       | empty'''
    p[0]=lex_value("State_machine_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)
        global curSymtable
        curSymtable=curSymtable.PrevTable

def p_state_decl(p):
    '''State_decl : State_decl_1 State_decl_2 STATE State_Lv6id State_decl_3 Data_def State_decl_4'''
    p[0]=lex_value("State_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.append(p[4])
    p[0].objects.extend(p[5].objects)
    p[0].objects.extend(p[6].objects)
    p[0].objects.extend(p[7].objects)
    global curSymtable
    symbol=Symbol(p[4].value,'State')
    curSymtable.setSymbol(p[4].value,symbol)

    symtable = SymbolTable(p[4].value,curSymtable)
    curSymtable.ChildTableList.append(symtable)
    curSymtable = symtable
    print("this state is",curSymtable.EnvName)

def p_state_decl_1(p):
    '''State_decl_1 : INITIAL
                    | empty'''
    p[0]=lex_value("State_decl_1")
    if p[1].strs=='initial':
        p[0].objects.append(p[1])


def p_state_decl_2(p):
    '''State_decl_2 : FINAL
                    | empty'''
    p[0]=lex_value("State_decl_2")
    if p[1].strs=='final':
        p[0].objects.append(p[1])


def p_state_decl_3(p):
    '''State_decl_3 : UNLESS State_decl_5
    | empty'''
    p[0]=lex_value("State_decl_3")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)

def p_state_decl_5(p):
    '''State_decl_5 : Transition SEMICOLON State_decl_6'''
    p[0]=lex_value("State_decl_5")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)

def p_state_decl_6(p):
    '''State_decl_6 : Transition SEMICOLON State_decl_6
    | empty'''
    p[0]=lex_value("State_decl_6")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)

def p_data_def(p):
    '''Data_def : Equation SEMICOLON
                | Scope'''
    p[0]=lex_value("Data_def")
    p[0].objects.extend(p[1].objects)
    if len(p)!=2:
        p[0].objects.append(p[2])


def p_scope(p):
    '''Scope : Signal_block_zero_or_one Local_block_zero_or_one Eqs
    | Signal_block_zero_or_one Local_block_zero_or_one'''
    #未完成
    p[0]=lex_value("Scope")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)
    if len(p)==4:
        p[0].objects.extend(p[3].objects)


#Equation_zero_or_more_with_semicolon需要进行拓扑排序
def p_eqs(p):
    'Eqs : LET Equation_zero_or_more_with_semicolon TEL'
    p[0]=lex_value("Eqs")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])


def p_state_decl_4(p):
    '''State_decl_4 : UNTIL State_decl_6 State_decl_7
                    | empty '''
    p[0]=lex_value("State_decl_4")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)

def p_state_decl_7(p):
    '''State_decl_7 : SYNCHRO State_decl_8 Fork SEMICOLON
    | empty'''
    p[0]=lex_value("State_decl_7")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])

def p_state_decl_8(p):
    '''State_decl_8 : Actions
    | empty'''
    p[0]=lex_value("State_decl_8")
    if p[1].strs=='Actions':
        p[0].objects.extend(p[1].objects)

def p_transition(p):
    '''Transition : IF Expr Arrow'''
    p[0]=lex_value("Transition")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)


def p_arrow(p):
    '''Arrow : Actions Fork
    | Fork'''
    p[0]=lex_value("Arrow")
    if len(p)==2:
        p[0].objects.extend(p[1].objects)
    else:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_fork(p):
    '''Fork : Target
    | IF Expr Arrow Fork_1 Fork_2 END'''
    p[0]=lex_value("Fork")
    if len(p)==2:
        p[0].objects.extend(p[1].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
        p[0].objects.extend(p[4].objects)
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])

def p_fork_1(p):
    '''Fork_1 : Elsif_fork Fork_1
    | empty'''
    p[0]=lex_value("Fork_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_fork_2(p):
    '''Fork_2 : Else_fork
    | empty'''
    p[0]=lex_value("Fork_2")
    if p[1].strs=='Else_fork':
        p[0].objects.extend(p[1].objects)

def p_elsif_fork(p):
    '''Elsif_fork : ELSIF Expr Arrow'''
    p[0]=lex_value("Elsif_fork")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)

def p_else_fork(p):
    '''Else_fork : ELSE Arrow'''
    p[0]=lex_value("Else_fork")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_target(p):
    '''Target : RESTART LV6ID
    | RESUME LV6ID'''
    p[0]=lex_value("Target")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])

def p_actions(p):
    '''Actions : DO LBPARENTHESE Actions_1 Emission_body Actions_2 RBPARENTHESE
    | DO Data_def'''
    p[0]=lex_value("Actions")
    if len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.extend(p[4].objects)
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])

def p_actions_1(p):
    '''Actions_1 : EMIT
    | empty'''
    p[0]=lex_value("Actions_1")
    if p[1].strs=='emit':
        p[0].objects.append(p[1])

def p_actions_2(p):
    '''Actions_2 : SEMICOLON Actions_1 Emission_body Actions_2
    | empty'''
    p[0]=lex_value("Actions_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
        p[0].objects.extend(p[4].objects)

def p_clocked_block(p):
    '''Clocked_block : ACTIVATE Id_zero_or_one If_block
    | ACTIVATE Id_zero_or_one Match_block'''
    p[0]=lex_value("Clocked_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)

    global curSymtable
    curSymtable=curSymtable.PrevTable



def p_id_zero_or_one(p):
    '''Id_zero_or_one : LV6ID
    | empty'''
    p[0]=lex_value("Id_zero_or_one")
    tmpName=""
    global curSymtable
    if p[1].strs=='lv6id':
        tmpName = p[1].value
        p[0].objects.append(p[1])
    else:
        tmpName = getName('Control_block',curSymtable)
    symbol=Symbol(tmpName)
    curSymtable.setSymbol(tmpName,symbol)

    symtable=SymbolTable(tmpName)
    symtable.PrevTable=curSymtable
    curSymtable.ChildTableList.append(symtable)
    curSymtable=symtable
    print("this symbol Table is",curSymtable.EnvName)

def p_if_block(p):
    'If_block : IF Expr THEN If_block_1 ELSE If_block_1'
    p[0]=lex_value("If_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)
    p[0].objects.append(p[5])
    p[0].objects.extend(p[6].objects)


def p_if_block_1(p):
    '''If_block_1 : Data_def
    | If_block'''
    p[0]=lex_value("If_block_1")
    p[0].objects.extend(p[1].objects)


def p_match_block(p):
    '''Match_block : WHEN Expr MATCH Match_block_1'''
    p[0]=lex_value("Match_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)


def p_match_block_1(p):
    ' Match_block_1 : VERTICALBAR Pattern COLON Data_def1 Match_block_2 '
    p[0]=lex_value("Match_block_1")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)
    p[0].objects.extend(p[5].objects)

def p_match_block_2(p):
    '''Match_block_2 : VERTICALBAR Pattern COLON Data_def1 Match_block_2
    | empty'''
    p[0]=lex_value("Match_block_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.append(p[3])
        p[0].objects.extend(p[4].objects)
        p[0].objects.extend(p[5].objects)

#为了避免symbol的Code被覆盖
def p_data_def_1(p):
    'Data_def1 : Data_def'
    p[0]=lex_value("Data_def1")
    p[0].objects.extend(p[1].objects)


#若左边的符号为_或()则删去
def p_simple_equation(p):
    '''Simple_equation : Lhs EQU Expr'''
    p[0]=lex_value("Simple_equation")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)

def p_lhs(p):
    '''Lhs : LPARENTHESE RPARENTHESE
    | Lhs_id Lhs_1'''
    p[0]=lex_value("Lhs")
    if p[1].value!='(':
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])


def p_lhs_1(p):
    '''Lhs_1 : COMMA Lhs_id Lhs_1
    | empty'''
    p[0]=lex_value("Lhs_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


# not finish
def p_lhs_id(p):
    '''Lhs_id : LV6ID
              | UNDERLINE'''
    p[0]=lex_value("Lhs_id")   
    p[0].objects.append(p[1])


# not finish
def p_user_op_decl_1(p):
    '''User_op_decl_1 : Size_decl
                      | empty'''
    p[0]=lex_value("User_op_delc_1")
    if p[1].strs=='Size_decl':
        p[0].objects.extend(p[1].objects)


def p_size_decl(p):
    '''Size_decl : LSHIFT Id_one_or_more_with_comma RSHIFT 
                 | LSHIFT RSHIFT'''
    p[0]=lex_value("Size_decl")
    if len(p)!=3:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.append(p[3])
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        
def p_user_op_decl_2(p):
    '''User_op_decl_2 : Where_decl
                        | empty'''
    p[0]=lex_value("User_op_decl_2")
    if p[1].strs=='Where_decl':
        p[0].objects.extend(p[1].objects)

def p_where_decl(p):
    '''Where_decl : WHERE Typevar Where_decl_1 Numeric_kind'''
    p[0]=lex_value("Where_decl")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.extend(p[3].objects)
    p[0].objects.extend(p[4].objects)
    
def p_where_decl_1(p):
    '''Where_decl_1 : COMMA Typevar Where_decl_1
                    | empty'''
    p[0]=lex_value("Where_decl_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)

def p_typevar(p):
    '''Typevar : SINGLEQUOTE LV6ID'''
    p[0]=lex_value("Typevar")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])

def p_user_op_decl_3(p):
    '''User_op_decl_3 : Spec_decl
                        | empty'''
    #TODO:Spec_decl
    p[0]=lex_value("User_op_decl_3")
    if p[1].strs=='Spec_decl':
        p[0].objects.extend(p[1].objects)

def p_spec_decl(p):
    '''Spec_decl : SPECIALIZE Path_id'''
    p[0]=lex_value("Spec_decl")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])

def p_in_params(p):
    'In_Params : Params'
    p[0]=lex_value("In_Params")
    p[0].objects.extend(p[1].objects)

def p_out_params(p):
    'Out_Params : Params'
    p[0]=lex_value("Out_Params")
    p[0].objects.extend(p[1].objects)

def p_params(p):
    'Params : LPARENTHESE Params_1 RPARENTHESE'
    p[0]=lex_value("Params")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])

def p_params_1(p):
    '''Params_1 : Var_decls Params_2
    | empty'''
    p[0]=lex_value("Params_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_params_2(p):
    '''Params_2 : SEMICOLON Var_decls Params_2
    | empty'''
    p[0]=lex_value("Params_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


def p_var_decls(p):
    'Var_decls : Var_id Var_decls_1 COLON Type_expr Var_decls_2 Var_decls_3 Var_decls_4'
    p[0]=lex_value("Var_decls")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)
    p[0].objects.extend(p[5].objects)
    p[0].objects.extend(p[6].objects)
    p[0].objects.extend(p[7].objects)


def p_var_decls_1(p):
    '''Var_decls_1 : COMMA Var_id Var_decls_1
    | empty'''
    p[0]=lex_value("Var_decls_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)

def p_var_id(p):
    'Var_id : Var_id_1 Var_id_2 LV6ID'
    p[0]=lex_value("Var_id")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])

    global curSymtable
    symbol=Symbol(p[3].value)
    curSymtable.setSymbol(p[3].value,symbol)
    

def p_var_id_1(p):
    '''Var_id_1 : CLOCK
    | empty'''
    p[0]=lex_value("Var_id_1")
    if p[1].strs=='clock':
        p[0].objects.append(p[1])


def p_var_id_2(p):
    '''Var_id_2 : PROBE
    | empty'''
    p[0]=lex_value("Var_id_2")
    if p[1].strs=='probe':
        p[0].objects.append(p[1])


# not finish
def p_var_decls_2(p):
    '''Var_decls_2 : When_decl
                    | empty'''
    #TODO:when_decl未完成
    p[0]=lex_value("Var_decls_2")
    if p[1].strs=='When_decl':
        p[0].objects.extend(p[1].objects)

def p_when_decl(p):
    '''When_decl : WHEN Clock_expr'''
    #TODO:未完成
    p[0]=lex_value("When_decl")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)

def p_clock_expr(p):
    '''Clock_expr : LV6ID
    | NOT LV6ID
    | LPARENTHESE LV6ID MATCH Pattern RPARENTHESE'''
    #TODO:未完成
    p[0]=lex_value("Clock_expr")
    if len(p)==2:
        p[0].objects.append(p[1])
    elif len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.append(p[3])
        p[0].objects.extend(p[4].objects)
        p[0].objects.append(p[5])

def p_var_decls_3(p):
    '''Var_decls_3 : Default_decl
    | empty'''
    p[0]=lex_value("Var_decls_3")
    if p[1].strs=='Default_decl':
        p[0].objects.extend(p[1].objects)


def p_default_decl(p):
    '''Default_decl : DEFAULT EQU Expr'''
    p[0]=lex_value("Default_decl")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)


def p_var_decls_4(p):
    '''Var_decls_4 : Last_decl
    | empty'''
    p[0]=lex_value("Var_decls_4")
    if p[1].strs=='Last_decl':
        p[0].objects.extend(p[1].objects)

def p_last_decl(p):
    '''Last_decl : LAST EQU Expr'''
    p[0]=lex_value("Last_decl")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)


def p_package(p):
    'Package : PACKAGE'
    p[0]=lex_value("Package")
    p[0].objects.append(p[1])


def p_const_block(p):
    'Const_block : CONST Const_block_1'
    p[0]=lex_value("Const_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    if curSymtable.EnvName=='Global':
        global rootSymbol
        rootSymbol.Code.append(lexObjectsToString(p[0].objects))
    else:
        packageSymbol=curSymtable.PrevTable.getSymbolInThisEnv(curSymtable.EnvName)
        packageSymbol.Code.append(lexObjectsToString(p[0].objects))


def p_const_block_1(p):
    '''Const_block_1 : Const_decl SEMICOLON Const_block_1
    | empty'''
    p[0]=lex_value("Const_block_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)


def p_const_decl(p):
    '''Const_decl : Interface_status LV6ID COLON Type_expr EQU Expr
    | Interface_status LV6ID COLON Type_expr'''
    p[0]=lex_value("Const_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)
    if len(p)==7:
        p[0].objects.append(p[5])
        p[0].objects.extend(p[6].objects)
    symbol=Symbol(p[2].value,'Const')
    global curSymtable
    curSymtable.setSymbol(p[2].value,symbol)


def p_interface_status(p):
    '''Interface_status : Visibility_zero_or_one External
    | Visibility_zero_or_one'''
    p[0]=lex_value("Interface_status")
    p[0].objects.extend(p[1].objects)
    if len(p)!=2:
        p[0].objects.extend(p[2].objects)


def p_visibility_zero_or_one(p):
    '''Visibility_zero_or_one : Visibility
    | empty'''
    p[0]=lex_value("Visibility_zero_or_one")
    if p[1].strs=='Visibility':
        p[0].objects.extend(p[1].objects)


def p_external(p):
    'External : IMPORTED'
    p[0]=lex_value("External")
    p[0].objects.append(p[1])


def p_visibility(p):
    '''Visibility : PRIVATE
    | PUBLIC'''
    p[0]=lex_value("Visibility")
    p[0].objects.append(p[1])


def p_sensor_block(p):
    'Sensor_block : SENSOR Sensor_block_1'
    p[0]=lex_value("Sensor_block")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    # tmpstr = p[1].value + lexObjectsToString(p[2].objects)
    # p[0].Code.append(tmpstr)
    if curSymtable.EnvName=='Global':
        global rootSymbol
        rootSymbol.Code.append(lexObjectsToString(p[0].objects))
    else:
        packageSymbol=curSymtable.PrevTable.getSymbolInThisEnv(curSymtable.EnvName)
        packageSymbol.Code.append(lexObjectsToString(p[0].objects))


def p_sensor_block_1(p):
    '''Sensor_block_1 : Sensor_decl SEMICOLON Sensor_block_1
    | empty'''
    p[0]=lex_value("Sensor_block_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[2].objects)


def p_sensor_decl(p):
    'Sensor_decl : Id_one_or_more_with_comma COLON Type_expr'
    p[0]=lex_value("Sensor_decl")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)


def p_id_one_or_more_with_comma(p):
    'Id_one_or_more_with_comma : LV6ID Id_one_or_more_with_comma_1'
    p[0]=lex_value("Id_one_or_more_with_comma")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    global curSymtable
    symbol = Symbol(p[1].value,'Size')
    curSymtable.setSymbol(p[1].value,symbol)


def p_id_one_or_more_with_comma_1(p):
    '''Id_one_or_more_with_comma_1 : COMMA LV6ID Id_one_or_more_with_comma_1
    | empty'''
    p[0]=lex_value("Id_one_or_more_with_comma_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        global curSymtable
        symbol=Symbol(p[2].value,'Size')
        curSymtable.setSymbol(p[2].value,symbol)


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
    p[0]=lex_value("Type_expr")
    if len(p)==2:
        if p[1].strs=='Typevar':
            p[0].objects.extend(p[1].objects)
        else:
            p[0].objects.append(p[1])
    elif len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    else:
        if p[1].strs=='{':
            p[0].objects.append(p[1])
            p[0].objects.extend(p[2].objects)
            p[0].objects.extend(p[3].objects)
            p[0].objects.append(p[4])
        else:
            p[0].objects.extend([p[1],p[2],p[3],p[4]])


def p_type_expr_1(p):
    '''Type_expr_1 : COMMA Field_decl Type_expr_1
    | empty'''
    p[0]=lex_value("Type_expr_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


def p_field_decl(p):
    '''Field_decl : LV6ID COLON Type_expr'''
    p[0]=lex_value("Field_decl")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)

def p_path_1(p):
    '''Path_1 : DOUBLECOLON LV6ID Path_1
    | empty '''
    p[0]=lex_value("Path_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    
def p_path_id(p):
    '''Path_id : LV6ID Path_1'''
    p[0]=lex_value("pathId")
    tmpStr=p[1].value
    for elem in p[2].objects:
        tmpStr+=elem.value
    p[0].value=tmpStr

def p_id_expr(p):
    '''Id_expr : Path_id
    | SINGLEQUOTE LV6ID
    | LAST SINGLEQUOTE LV6ID'''
    p[0]=lex_value("Id_expr")
    if len(p)==2:
        p[0].objects.append(p[1])
    elif len(p)==3:
        p[2].strs='singlequoteLv6id'
        p[0].objects.extend([p[1],p[2]])
    else:
        p[3].strs='lastSinglequoteLv6id'
        p[0].objects.extend([p[1],p[2],p[3]])


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
    p[0]=lex_value("Expr")
    p[0].objects.extend(p[1].objects)


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
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    elif len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
    elif len(p)==8:
        p[0].objects.extend([p[1],p[2]])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])
        p[0].objects.extend(p[7].objects)
        p[0].objects.append(p[8])
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])
        p[0].objects.extend(p[7].objects)
        p[0].objects.append(p[8])

def p_tempo_expr_1(p):
    '''Tempo_expr_1 : SEMICOLON List Tempo_expr_1
                    | empty'''
    p[0]=lex_value("Tempo_expr_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)

def p_relation_expr(p):
    '''Relation_expr : Expr EQU Expr
    | Expr NOEQU Expr
    | Expr LESS Expr
    | Expr GREATER Expr
    | Expr LESSEQU Expr
    | Expr GREATEREQU Expr'''
    # print("Relation_expr")
    p[0]=lex_value("Relation_expr")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)

# 往符号表添加一个局部变量存储if表达式的结果。if (boolExpr){ localVar=Expr1;}else{ localVar=Expr2;}
def p_switch_expr(p):
    '''Switch_expr : IF Expr THEN Expr ELSE Expr
    | LPARENTHESE CASE Expr OF Switch_expr_1 RPARENTHESE'''
    # print("Swith_expr")
    p[0]=lex_value("Switch_expr")
    if p[1].strs=='if':
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.append(p[3])
        p[0].objects.extend(p[4].objects)
        p[0].objects.append(p[5])
        p[0].objects.extend(p[6].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])

def p_switch_expr_1(p):
    'Switch_expr_1 : Case_expr Switch_expr_2'
    p[0]=lex_value("Switch_expr_1")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)


def p_switch_expr_2(p):
    '''Switch_expr_2 : Case_expr Switch_expr_2
    | empty'''
    p[0]=lex_value("Switch_expr_2")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)


def p_case_expr(p):
    'Case_expr : VERTICALBAR Pattern COLON Expr'
    p[0]=lex_value("Case_expr")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)


def p_pattern(p):
    '''Pattern : Path_id
    | CHARACTER
    | Pattern_1 INTEGERNUM
    | Pattern_1 TYPED_INTEGER
    | Bool_atom
    | UNDERLINE'''
    p[0]=lex_value("Pattern")
    if len(p)==3:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
    elif p[1].strs=='Bool_atom':
        p[0].objects.extend(p[1].objects)
    else:
        p[0].objects.append(p[1])


def p_pattern_1(p):
    '''Pattern_1 : MINUS
    | empty'''
    p[0]=lex_value("Pattern_1")
    if p[1].strs=='-':
        p[0].objects.append(p[1])

def p_arith_expr(p):
    '''Arith_expr : LPARENTHESE Expr COLON Type_expr RPARENTHESE'''
    # print("Arith_expr1")
    p[0]=lex_value("Arith_expr1")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)
    p[0].objects.append(p[5])


def p_arith_expr_unary(p):
    '''Arith_expr : MINUS Expr %prec UMINUS
    | PLUS Expr %prec UPLUS
    | LNOT Expr'''
    # print("Arith_expr2")
    p[0]=lex_value("Arith_expr2")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)


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
    p[0]=lex_value("Arith_expr3")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)

def p_apply_expr(p):
    '''Apply_expr : Operator LPARENTHESE List RPARENTHESE'''
    opStr=lexObjectsToString(p[1].objects)
    node=graphTree(opStr,"applyFunc")
    global curNode
    curNode.son.append(node)

    p[0]=lex_value("Apply_expr")

    tmpStr=""
    for elem in p[1].objects:
        if elem.strs=='pathId':
            elem.strs='operatorLv6id'
            tmpStr=elem.value
            if curSymtable.getSymbolInThisEnv(tmpStr)==None:
                preSymtable=curSymtable.PrevTable
                preOpKindSymbol=preSymtable.getSymbolInThisEnv(curSymtable.EnvName)
                preOpKindSymbol.relyList.append(tmpStr)

    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)
    p[0].objects.append(p[4])
    
# not finish
def p_prefix(p):
    '''Prefix : Path_id
    | PREFIXOP'''
    #TODO:PREFIXOP没有添加，PREFIXOP需要在scade_lex.py里面添加
    p[0]=lex_value("Prefix")
    p[0].objects.append(p[1])

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
    p[0]=lex_value("Operator")
    if len(p)==2:
        p[0].objects.extend(p[1].objects)
    elif len(p)==5:
        p[0].objects.extend([p[1],p[2],p[3],p[4]])
    elif len(p)==6:
        p[0].objects.extend([p[1],p[2],p[3]])
        p[0].objects.extend(p[4].objects)
        p[0].objects.append(p[5])
    elif len(p)==7:
        if p[2].strs=='activate':
            p[0].objects.extend([p[1],p[2]])
            p[0].objects.extend(p[3].objects)
            p[0].objects.append(p[4])
            p[0].objects.extend(p[5].objects)
            p[0].objects.append(p[6])
        else:
            p[0].objects.append(p[1])
            p[0].objects.extend(p[2].objects)
            p[0].objects.append(p[3])
            p[0].objects.extend(p[4].objects)
            p[0].objects.extend([p[5],p[6]])
            # print("map",p[0].objects)
    elif len(p)==8:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.extend([p[6],p[7]])
    elif len(p)==9:
        p[0].objects.extend([p[1],p[2]])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])
        p[0].objects.extend(p[7].objects)
        p[0].objects.append(p[8])
    elif len(p)==10:
        p[0].objects.extend([p[1],p[2]])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.extend([p[6],p[7]])
        p[0].objects.extend(p[8].objects)
        p[0].objects.append(p[9])
    elif len(p)==12:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.extend([p[6],p[7]])
        p[0].objects.extend(p[8].objects)
        p[0].objects.append(p[9])
        p[0].objects.extend(p[10].objects)
        p[0].objects.append(p[11])

def p_operator_1(p):
    '''Operator_1 : Expr Operator_2
    | empty'''
    p[0]=lex_value("Operator_1")
    if len(p)!=2:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_operator_2(p):
    '''Operator_2 : COMMA Expr Operator_2
    | empty'''
    p[0]=lex_value("Operator_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)

def p_iterator(p):
    '''Iterator : MAP
    | FOLD
    | MAPI
    | FOLDI
    | MAPFOLD
    | MAPFOLD INTEGERNUM
    | MAPFOLDI
    | MAPFOLDI INTEGERNUM'''
    p[0]=lex_value("Iterator")
    p[0].objects.append(p[1])
    if len(p)==3:
        p[0].objects.append(p[2])

def p_iterator_mw(p):
    '''Iterator_mw : MAPW
    | MAPWI
    | MAPFOLDW
    | MAPFOLDW INTEGERNUM
    | MAPFOLDWI
    | MAPFOLDWI INTEGERNUM'''
    p[0]=lex_value("Iterator_mw")
    p[0].objects.apend(p[1])
    if len(p)==3:
        p[0].objects.append(p[2])


def p_list_expr(p):
    '''List_expr : LPARENTHESE List RPARENTHESE'''
    # print("List_expr")
    p[0]=lex_value("List_expr")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])


def p_list(p):
    '''List : List_1
    | empty'''
    p[0]=lex_value("List")
    if p[1].strs=='List_1':
        p[0].objects.extend(p[1].objects)


def p_list_1(p):
    '''List_1 : Expr List_2'''
    p[0]=lex_value("List_1")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)

def p_list_2(p):
    '''List_2 : COMMA Expr List_2
    | empty'''
    p[0]=lex_value("List_2")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


# typed_integer和typed_float未添加
def p_atom(p):
    '''Atom : Bool_atom
    | INTEGERNUM
    | FLOATNUM
    | CHARACTER
    | TYPED_INTEGER
    | TYPED_FLOAT'''
    p[0]=lex_value("Atom")
    if p[1].strs=='Bool_atom':
        p[0].objects.extend(p[1].objects)
    else:
        p[0].objects.append(p[1])


def p_bool_atom(p):
    '''Bool_atom : TRUE
    | FALSE'''
    p[0]=lex_value("Bool_atom")
    p[0].objects.append(p[1])


def p_bool_expr(p):
    '''Bool_expr : NOT Expr
    | HASHTAG LPARENTHESE List RPARENTHESE'''
    # print("Bool_expr1")
    p[0]=lex_value("Bool_expr1")
    if len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])


def p_bool_expr_bin(p):
    '''Bool_expr : Expr AND Expr
    | Expr OR Expr
    | Expr XOR Expr'''
    # print("Bool_expr2")
    p[0]=lex_value("Bool_expr")
    p[0].objects.extend(p[1].objects)
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)


def p_struct_expr(p):
    '''Struct_expr : Expr POINT LV6ID
    | LBPARENTHESE Label_expr Struct_expr_1 RBPARENTHESE'''
    # print("Struct_expr")
    p[0]=lex_value("Struct_expr")
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    else:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])


def p_struct_expr_1(p):
    '''Struct_expr_1 : COMMA Label_expr Struct_expr_1
    | empty'''
    p[0]=lex_value("Struct_expr_1")
    if len(p)!=2:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.extend(p[3].objects)


def p_label_expr(p):
    '''Label_expr : LV6ID COLON Expr'''
    p[0]=lex_value("Label_expr")
    p[0].objects.append(p[1])
    p[0].objects.append(p[2])
    p[0].objects.extend(p[3].objects)

def p_array_expr(p):
    '''Array_expr : LBRACKET List RBRACKET
    | Expr Index'''
    # print("Array_expr1")
    p[0]=lex_value("Array_expr1")
    if len(p)==4:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.append(p[3])
    else:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_array_expr2(p):
    '''Array_expr : REVERSE Expr
    | Expr AT Expr'''
    # print("Array_expr2")
    p[0]=lex_value("Array_expr2")
    if len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
    else:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)

def p_array_expr3(p):
    '''Array_expr : Expr EXPONENT Expr
    | Expr LBRACKET Expr TPOINT Expr RBRACKET'''
    p[0]=lex_value("Array_expr3")
    if len(p)==4:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
    else:
        p[0].objects.extend(p[1].objects)
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.append(p[4])
        p[0].objects.extend(p[5].objects)
        p[0].objects.append(p[6])

def p_array_expr4(p):
    '''Array_expr : LPARENTHESE Expr POINT Array_expr_1 DEFAULT Expr RPARENTHESE
    | TRANSPOSE LPARENTHESE Expr SEMICOLON INTEGERNUM SEMICOLON INTEGERNUM RPARENTHESE'''
    p[0]=lex_value("Array_expr4")
    if len(p)==8:
        p[0].objects.append(p[1])
        p[0].objects.extend(p[2].objects)
        p[0].objects.append(p[3])
        p[0].objects.extend(p[4].objects)
        p[0].objects.append(p[5])
        p[0].objects.extend(p[6].objects)
        p[0].objects.append(p[7])
    else:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
        p[0].objects.extend(p[3].objects)
        p[0].objects.extend([p[4],p[5],p[6],p[7],p[8]])

def p_array_expr_1(p):
    '''Array_expr_1 : Label_or_index Array_expr_2'''
    p[0]=lex_value("Array_expr_1")
    p[0].objects.extend(p[1].objects)
    p[0].objects.extend(p[2].objects)

def p_array_expr_2(p):
    '''Array_expr_2 : Label_or_index Array_expr_2
    | empty'''
    p[0]=lex_value("Array_expr_2")
    if len(p)==3:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_label_or_index(p):
    '''Label_or_index : POINT LV6ID
    | Index'''
    p[0]=lex_value("Label_or_index")
    if len(p)==3:
        p[0].objects.append(p[1])
        p[0].objects.append(p[2])
    else:
        p[0].objects.extend(p[1].objects)

def p_index(p):
    '''Index : LBRACKET Expr RBRACKET'''
    p[0]=lex_value("Index")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])

def p_mixed_constructor(p):
    '''Mixed_constructor : LPARENTHESE Expr WITH Mixed_constructor_1 EQU Expr RPARENTHESE'''
    #TODO:未完成
    # print("Mixed_constructor")
    p[0]=lex_value("Mixed_constructor")
    p[0].objects.append(p[1])
    p[0].objects.extend(p[2].objects)
    p[0].objects.append(p[3])
    p[0].objects.extend(p[4].objects)
    p[0].objects.append(p[5])
    p[0].objects.extend(p[6].objects)
    p[0].objects.append(p[7])

def p_mixed_constructor_1(p):
    '''Mixed_constructor_1 : Label_or_index Mixed_constructor_2'''
    p[0]=lex_value("Mixed_constructor_1")
    if len(p)==3:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_mixed_constructor_2(p):
    '''Mixed_constructor_2 : Label_or_index Mixed_constructor_2
    | empty'''
    p[0]=lex_value("Mixed_constructor_2")
    if len(p)==3:
        p[0].objects.extend(p[1].objects)
        p[0].objects.extend(p[2].objects)

def p_error(p):
    print("Syntax error in input!")


def p_empty(p):
    'empty :'
    p[0] = lex_value('Empty')

def get_parse(filename):
    global program
    parser = yacc(debug=1)

    file = open(filename,'r')
    strs=file.read()

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
    # writeFile(programNode)

    content=""
    for elem in rootSymbol.Code:
        content+=elem
    
    output_filename = os.path.splitext(os.path.basename(filename))[0]
    file=open(f"stage1_{output_filename}.scade",'w')
    file.write(content)
    print(f"output_file path: stage1_{output_filename}.scade")#不能删除，run.sh脚本中使用了
    
if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i','--input_path',required=True,type=str)
    args = argParser.parse_args()
    get_parse(args.input_path)
    # parser.parse(strs, lexer=scade_lexer)


#package airdynamic有问题