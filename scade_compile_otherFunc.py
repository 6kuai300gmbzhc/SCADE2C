import copy
import queue
from SymbolClass import Symbol, SymbolTable, fbyClass
from scade_lex import scade_lex, get_tokens, tokens, lex_value

intArr = ["int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64"]
floatArr = ["float32", "float64"]
typeArr=['bool','int8','int16','int64','int32','uint8','uint16','uint32','uint64','float32','float64','char','enum','array','struct']

isPackage = 0
# global isStatemachine
isStatemachine = 0

packageName = "" # 用于记录当前需要添加的包后缀，如"_P1_P2"
packageList = list() # 用于记录当前进入的包的名称，如["P1", "P2"]
op_kind_id = ""
op_kind = ""

scade_lexer = scade_lex()
GlobalEnv = SymbolTable('Global')  #global的符号表中的符号为各个函数的函数名，该符号只填充了Returns,Params,isStatemachine,hasInternalState
                                   #global的符号表中还有子符号表，名为其子函数名的符号表，各个Package的符号表
thisEnv = GlobalEnv
program = None

# 全局变量，用于存储被调用过的函数名称
calledOperators = []


class Node:
    def __init__(self,type=''):
        self.type=type#type能为ifCondition,switchCondition,equation,fbyBlock,ifBlock
        self.childNodeList=list()
        self.pattern=list()
        self.value=list()

class topologyNode:
    def __init__(self,name='',index=0,tpIdx=0,inNum=0,outNum=0):
        self.name=name
        self.index=index
        self.tpIdx=tpIdx
        self.inNum=inNum
        self.outNum=outNum
        self.finish=False

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
def topologyReady(symbolList):
    adjList=[]
    nodeDict={}
    nodeList=[]
    num=0
    for idx in range(0,len(symbolList)):
        leftName=symbolList[idx].Name
        if leftName not in nodeDict.keys():
            node=topologyNode(leftName,num,idx)
            nodeList.append(node)
            nodeDict[leftName]=num
            num+=1
            adjList.append([])
        else:
            raise NotImplementedError('%s redefined'%leftName)
    for elem in symbolList:
        adjIdx1=nodeDict[elem.Name]
        for relyElem in elem.relyList:
            if relyElem in nodeDict.keys():
                adjIdx2=nodeDict[relyElem]
                nodeList[adjIdx1].inNum+=1
                nodeList[adjIdx2].outNum+=1
                adjList[adjIdx2].append(adjIdx1)
    return topologySort(symbolList,adjList,nodeList)
    
def getIdType(symbolName,symbolTable):
    symbol=symbolTable.getSymbolInThisEnv(symbolName)
    if symbol!=None and symbol.Type not in typeArr:
        if symbol.Type[0]=='\'':
            return symbolTable.getSymbolInThisEnv(symbol.Type)
        else:
            rootSymbolTable=GlobalEnv
            return getIdType(symbol.Type,rootSymbolTable)
    else:
        return symbol

def getStructElemType(lex,symtable):
    symbol = getIdType(lex.value, symtable)
    for idx in range(len(lex.objects)):
        if idx != len(lex.objects) - 1:
            symbol = symbol.FieldList[lex.objects[idx].value]
            while symbol.Type not in typeArr:
                symbol = GlobalEnv.getSymbolInThisEnv(symbol.Type)
        else:
            return symbol.FieldList[lex.objects[idx].value]

def checkElemInStruct(symbolName,params,idx,thisEnv):
    if idx >= len(params):
        return True
    realSymbol=getIdType(symbolName,thisEnv)
    if params[idx].value not in realSymbol.FieldList:
        return False
    else:
        return checkElemInStruct(realSymbol.FieldList[params[idx].value].Type,params,idx+1,thisEnv)
    
def objectsToString(objects,thisEnv,op_kind_id):
    sstr=""
    if thisEnv.PrevTable!=None:
        globalSymbol=thisEnv.PrevTable.getSymbolInThisEnv(op_kind_id)
    for elem in objects:
        symbol=thisEnv.getSymbolInThisAndPreEnv(elem.value)
        #没有被调用，或者被调用了，且是node，则可以使用outC
        if elem.strs=='lv6id' and ((not globalSymbol.isCalled) or (globalSymbol.isCalled and globalSymbol.hasInternalState==True) ):    
            # type=symbol.Type
            if symbol.IsReturn:
                sstr+=symbol.changeName(thisEnv)
            else:
                if globalSymbol.isCalled:
                    sstr+=symbol.Name
                else:
                    sstr+=symbol.changeName(thisEnv)
            if len(elem.arrSize)!=0:
                sstr+=objectsToString(elem.arrSize,thisEnv,op_kind_id)
            if len(elem.objects)!=0:
                if checkElemInStruct(symbol.Name,elem.objects,0,thisEnv):
                    for structElem in elem.objects:
                        sstr+=".%s"%structElem.value
        elif elem.strs=='lv6id':
            if len(globalSymbol.Returns) != 1:
                if symbol.Name in globalSymbol.Returns and (symbol.Type in intArr or symbol.Type in floatArr or symbol.Type=='bool'):
                    sstr+="*"
            sstr+=symbol.Name
        elif elem.strs=='Path_id':
            # print("symbol.Kind=",symbol.Kind)
            sstr+=elem.value
            # sstr+=symbol.changeName(thisEnv)
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
        else:
            sstr+=elem.value
    return sstr

def getArrSize(objects):
    str = ""
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

def getArrSizeList(objects):
    retList=[]
    for obj in objects:
        str=''
        for elem in obj:
            str+=elem.value
        retList.append(eval(str))
    # retList.reverse()
    return retList

def getArrIdx(arrSizeList,idxList,stIdx,idxStrList):
    if stIdx==len(idxList)-1:
        for idx in range(0,arrSizeList[-1]):
            idxList[stIdx]=idx
            tmpStr=''
            for elem in idxList:
                tmpStr+='[%s]'%str(elem)
            idxStrList.append(tmpStr)
        return
    for idx in range(0,arrSizeList[stIdx]):
        idxList[stIdx]=idx 
        getArrIdx(arrSizeList,idxList,stIdx+1,idxStrList)


def typeToString(symbol,leftLex,symtable,op_kind_id):
    str=""
    leftName=objectsToString(leftLex,symtable,op_kind_id)
    if symbol.StateType=='equation':
        str+=leftName
        str+=' = '
        str+=objectsToString(symbol.Code,symtable,op_kind_id)
        str+=';\n'
    elif symbol.StateType=='memcpy':
        str+='memcpy(&%s,&%s,sizeof(%s));\n'%(leftName,objectsToString(symbol.Code,symtable,op_kind_id),symbol.Type)
    elif symbol.StateType=='ifCondition':
        ifNode=symbol.Code[0]
        str+=blockToString(ifNode,leftName,symtable,op_kind_id)
    elif symbol.StateType=='switchCondition':
        switchNode=symbol.Code[0]
        str+=blockToString(switchNode,leftName,symtable,op_kind_id)
    elif symbol.StateType=='fbyBlock':
        str+="if(%s){\n for(int idx=0;idx<%s;idx++){\n"%(objectsToString(symbol.Code[0],symtable,op_kind_id),objectsToString(symbol.Code[4],symtable,op_kind_id))
        str+="%s[idx]=%s;\n}\n"%(objectsToString(symbol.Code[2],symtable,op_kind_id),objectsToString(symbol.Code[5],symtable,op_kind_id))
        str+="%s=0;\n"%objectsToString(symbol.Code[1],symtable,op_kind_id)
        str+="}\n"
        str+="%s=%s[%s];\n"%(leftName,objectsToString(symbol.Code[2],symtable,op_kind_id),objectsToString(symbol.Code[1],symtable,op_kind_id))
        str+="%s[%s]=%s;\n"%(objectsToString(symbol.Code[2],symtable,op_kind_id),objectsToString(symbol.Code[1],symtable,op_kind_id),objectsToString(objectsToString(symbol.Code[3],symtable,op_kind_id)))
        str+="%s=(%s+1)%%(%s);\n"%(objectsToString(symbol.Code[1],symtable,op_kind_id),objectsToString(symbol.Code[1],symtable,op_kind_id),objectsToString(symbol.Code[4],symtable,op_kind_id))
    elif symbol.StateType=='struct':
        for key,value in symbol.FieldValueList.items():
            tmpLex=[]
            tmpLex.extend(leftLex)
            objects=key.split('.')
            for elem in objects:
                tmpLex.append(lex_value('',"."+elem))
            str+=typeToString(value,tmpLex,symtable,op_kind_id)
    elif symbol.StateType=='arrayList':
        arrSizeList=getArrSizeList(symbol.arrSize)
        idxList=[0 for _ in range(len(arrSizeList))]
        idxStrList=[]
        getArrIdx(arrSizeList,idxList,0,idxStrList)
        for idx in range(0,len(symbol.arrValueList)):
            leftLex.append(lex_value('',idxStrList[idx]))
            symbol.arrValueList[idx].Type=symbol.Type
            str+=typeToString(symbol.arrValueList[idx],leftLex,symtable,op_kind_id)
            leftLex.pop()
    elif symbol.StateType=='ApplyExpr':
        str+="%s("%symbol.Name
        for idx in range(len(symbol.Params)):
            if idx==0:
                str+="%s"%objectsToString([symbol.Params[idx]],symtable,op_kind_id)
            else:
                str+=",%s"%objectsToString([symbol.Params[idx]],symtable,op_kind_id)
        for idx in range(len(symbol.Returns)):
            if len(symbol.Params)==0:
                str+="&%s"%objectsToString([symbol.Returns[idx]],symtable,op_kind_id)
            else:
                str+=",&%s"%objectsToString([symbol.Returns[idx]],symtable,op_kind_id)
        str+=");\n"
    return str

def blockToString(root,leftName,symtable,op_kind_id):
    str=""
    if root.type=='ifCondition':
        str+="if(%s)"%(objectsToString(root.value,symtable,op_kind_id))
        if len(root.childNodeList)==1:
            leftNode=root.childNodeList[0]
            str+="{\n%s}\n"%blockToString(leftNode,leftName,symtable,op_kind_id)
        elif len(root.childNodeList)==2:
            leftNode=root.childNodeList[0]
            rightNode=root.childNodeList[1]
            str+="{\n%s}else{\n%s}\n"%(blockToString(leftNode,leftName,symtable,op_kind_id),blockToString(rightNode,leftName,symtable,op_kind_id))
    elif root.type=='equation':
        str+="%s = %s;\n"%(leftName,objectsToString(root.value,symtable,op_kind_id))
    elif root.type=='switchCondition':
        str += "switch(%s){\n" % (objectsToString(root.value, symtable,op_kind_id))
        isDefault = False
        for elem in root.childNodeList:
            if elem.pattern[0].value == '_':
                isDefault = True
                str += "default :\n{\n"
            else:
                str += "case %s :\n{\n" % objectsToString(elem.pattern, symtable,op_kind_id)
            str += "%s" % (blockToString(elem, leftName, symtable,op_kind_id))
            str += "break;\n}\n"
        if isDefault == False:
            str += "default :\nbreak;\n}\n"
    elif root.type=='fbyBlock':
        str += "if(%s){\n for(int idx=0;idx<%s;idx++){\n" % (
        objectsToString(root.value[0], symtable,op_kind_id), objectsToString(root.value[4], symtable,op_kind_id))
        str += "%s[idx]=%s;\n}\n" % (objectsToString(root.value[2], symtable,op_kind_id), objectsToString(root.value[5], symtable,op_kind_id))
        str += "%s=0;\n" % objectsToString(root.value[1], symtable,op_kind_id)
        str += "}\n"
        str += "%s=%s[%s];\n" % (
        leftName, objectsToString(root.value[2], symtable,op_kind_id), objectsToString(root.value[1], symtable,op_kind_id))
        str += "%s[%s]=%s;\n" % (objectsToString(root.value[2], symtable,op_kind_id), objectsToString(root.value[1], symtable,op_kind_id),
                                 objectsToString(root.value[3], symtable,op_kind_id))
        str += "%s=(%s+1)%%(%s);\n" % (objectsToString(root.value[1], symtable,op_kind_id), objectsToString(root.value[1], symtable,op_kind_id),
                                       objectsToString(root.value[4], symtable,op_kind_id))
    return str

def recursiveGetRely(type,node,tmpList):
    if type=='ifCondition':
        tmpList.extend(node.value)
        tmpList.extend(node.pattern)
        for elem in node.childNodeList:
            tmpNode=elem
            recursiveGetRely(tmpNode.type,tmpNode,tmpList)
    elif type=='equation':
        tmpList.extend(node.pattern)
        tmpList.extend(node.value)
    elif type=='switchCondition':
        tmpList.extend(node.value)
        for elem in node.childNodeList:
            tmpNode=elem
            recursiveGetRely(tmpNode.type,tmpNode,tmpList)
    elif type=='fbyBlock':
        tmpList.extend(node.value[3])
        tmpList.extend(node.value[4])
        tmpList.extend(node.value[5])
        tmpList.extend(node.pattern)

def getRely(symbol,symtable,relyList):
    tmpList=list()
    if symbol.StateType=='ifCondition':
        recursiveGetRely(symbol.StateType,symbol.Code[0],tmpList)
    elif symbol.StateType=='equation':
        tmpList.extend(symbol.Code)
    elif symbol.StateType=='fbyBlock':
        tmpList.extend(symbol.Code[3])
        tmpList.extend(symbol.Code[4])
        tmpList.extend(symbol.Code[5])
    elif symbol.StateType=='switchCondition':
        recursiveGetRely(symbol.StateType,symbol.Code[0],tmpList)
    elif symbol.StateType=='memcpy':
        tmpList.extend(symbol.Code)
    elif symbol.StateType=='struct':
        for _,value in symbol.FieldValueList.items():
            tmpList.extend(value.Code)
    elif symbol.StateType=='ApplyExpr':
        tmpList.extend(symbol.Params)
    for elem in tmpList:
        if elem.strs=='lv6id':
            tmpSymbol = symtable.getSymbolInThisEnv(elem.value)
            if tmpSymbol != None:
                if tmpSymbol.IsInput != True and tmpSymbol.Kind != 'Const' and tmpSymbol.Kind != 'Sensor':
                    relyList.append(elem.value)
