import copy
import queue

typeArr=['bool','int8','int16','int64','int32','uint8','uint16','uint32','uint64','float32','float64','char','enum','array','struct']
# class IfNode:
#     def __init__(self,type=''):
#         self.type=type#type可能为equation,condition,fbyBlock,ifBlock
#         self.left=None
#         self.right=None
#         self.initList=list()
#         self.value=list()
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

def getRootSymbolTable(thisEnv):
    if thisEnv.PrevTable!=None:
        return getRootSymbolTable(thisEnv.PrevTable)
    else:
        return thisEnv
def getIdType(symbolName,symbolTable):
    symbol=symbolTable.getSymbol(symbolName)
    if symbol!=None and symbol.Type not in typeArr:
        rootSymbolTable=getRootSymbolTable(symbolTable)
        return getIdType(symbol.Type,rootSymbolTable)
    else:
        return symbol
def checkElemInStruct(symbolName,params,idx,thisEnv):
    if idx >= len(params):
        return True
    realSymbol=getIdType(symbolName,thisEnv)
    if params[idx].value not in realSymbol.FieldList:
        return False
    else:
        return checkElemInStruct(realSymbol.FieldList[params[idx].value].Type,params,idx+1)
def objectsToString(objects,thisEnv):
    # type=""
    sstr=""
    for elem in objects:
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
#最初的转换时，node是symbol.ifTree。但若switch中嵌套if。则node是switch节点中value[0]
def typeToString(type,leftLex,rightList,symtable):
    str=""
    if len(leftLex.objects)==0:
        leftName=objectsToString([leftLex],symtable)
    if type=='equation':
        str+=leftName
        str+=' = '
        str+=objectsToString(rightList,symtable)
        str+=';\n'
    elif type=='ifCondition':
        ifNode=rightList[0]
        str+=blockToString(ifNode,leftName,symtable)
    elif type=='switchCondition':
        switchNode=rightList[0]
        str+=blockToString(switchNode,leftName,symtable)
    elif type=='fbyBlock':
        str+="if(%s){\n for(int idx=0;idx<%s;idx++){\n"%(objectsToString(rightList[0],symtable),objectsToString(rightList[4],symtable))
        str+="%s[idx]=%s;\n}\n"%(objectsToString(rightList[2],symtable),objectsToString(rightList[5],symtable))
        str+="%s=0;\n"%objectsToString(rightList[1],symtable)
        str+="}\n"
        str+="%s=%s[%s];\n"%(leftName,objectsToString(rightList[2],symtable),objectsToString(rightList[1],symtable))
        str+="%s[%s]=%s;\n"%(objectsToString(rightList[2],symtable),objectsToString(rightList[1],symtable),objectsToString(objectsToString(rightList[3],symtable)))
        str+="%s=(%s+1)%%(%s);\n"%(objectsToString(rightList[1],symtable),objectsToString(rightList[1],symtable),objectsToString(rightList[4],symtable))
    return str

def blockToString(root,leftName,symtable):
    str=""
    if root.type=='ifCondition':
        str+="if(%s)"%(objectsToString(root.value,symtable))
        if len(root.childNodeList)==1:
            leftNode=root.childNodeList[0]
            str+="{\n%s}\n"%blockToString(leftNode,leftName,symtable)
        elif len(root.childNodeList)==2:
            leftNode=root.childNodeList[0]
            rightNode=root.childNodeList[1]
            str+="{\n%s}else{\n%s}\n"%(blockToString(leftNode,leftName,symtable),blockToString(rightNode,leftName,symtable))
    elif root.type=='equation':
        str+="%s = %s;\n"%(leftName,objectsToString(root.value,symtable))
    elif root.type=='switchCondition':
        str += "switch(%s){\n" % (objectsToString(root.value, symtable))
        isDefault = False
        for elem in root.childNodeList:
            if elem.pattern[0].value == '_':
                isDefault = True
                str += "default :\n{\n"
            else:
                str += "case %s :\n{\n" % objectsToString(elem.pattern, symtable)
            str += "%s" % (blockToString(elem, leftName, symtable))
            str += "break;\n}\n"
        if isDefault == False:
            str += "default :\nbreak;\n}\n"
    elif root.type=='fbyBlock':
        str += "if(%s){\n for(int idx=0;idx<%s;idx++){\n" % (
        objectsToString(root.value[0], symtable), objectsToString(root.value[4], symtable))
        str += "%s[idx]=%s;\n}\n" % (objectsToString(root.value[2], symtable), objectsToString(root.value[5], symtable))
        str += "%s=0;\n" % objectsToString(root.value[1], symtable)
        str += "}\n"
        str += "%s=%s[%s];\n" % (
        leftName, objectsToString(root.value[2], symtable), objectsToString(root.value[1], symtable))
        str += "%s[%s]=%s;\n" % (objectsToString(root.value[2], symtable), objectsToString(root.value[1], symtable),
                                 objectsToString(root.value[3], symtable))
        str += "%s=(%s+1)%%(%s);\n" % (objectsToString(root.value[1], symtable), objectsToString(root.value[1], symtable),
                                       objectsToString(root.value[4], symtable))
    return str

def deepSearchForSwitch(leftLex,node,symtable):
    str=''
    if node.type=='condition':
        str+="switch(%s){\n"%(objectsToString(node.value,symtable))
        isDefault=False
        for elem in node.childNodeList:
            if elem.pattern[0].value=='_':
                isDefault=True
                str+="default :\n{\n"
            else:
                str+="case %s :\n{\n"%(objectsToString(elem.pattern,symtable))
            if elem.type=='switchBlock' or elem.type=='ifBlock':
                str+="%s"%(typeToString(elem.type,leftLex,elem.value[0],elem.value,symtable))
            else:
                str+="%s"%(typeToString(elem.type,leftLex,elem,elem.value,symtable))
            str+="break;\n}\n"
        if isDefault==False:
            str+="default :\nbreak;\n}\n"
    return str

def setRely(type,node,tmpList):
    if type=='ifCondition':
        tmpList.extend(node.value)
        tmpList.extend(node.pattern)
        for elem in node.childNodeList:
            tmpNode=elem
            setRely(tmpNode.type,tmpNode,tmpList)
    elif type=='equation':
        tmpList.extend(node.pattern)
        tmpList.extend(node.value)
    elif type=='switchCondition':
        tmpList.extend(node.value)
        for elem in node.childNodeList:
            tmpNode=elem
            setRely(tmpNode.type,tmpNode,tmpList)
    elif type=='fbyBlock':
        tmpList.extend(node.value[3])
        tmpList.extend(node.value[4])
        tmpList.extend(node.value[5])
        tmpList.extend(node.pattern)
def getRely(symbol,symtable,relyList):
    tmpList=list()
    if symbol.StateType=='ifCondition':
        setRely(symbol.StateType,symbol.Code[0],tmpList)
    elif symbol.StateType=='equation':
        tmpList.extend(symbol.Code)
    elif symbol.StateType=='fbyBlock':
        tmpList.extend(symbol.Code[3])
        tmpList.extend(symbol.Code[4])
        tmpList.extend(symbol.Code[5])
    elif symbol.StateType=='switchCondition':
        setRely(symbol.StateType,symbol.Code[0],tmpList)
    for elem in tmpList:
        if elem.strs=='lv6id':
            tmpSymbol = symtable.getSymbol(elem.value)
            if tmpSymbol != None:
                if tmpSymbol.IsInput != True and tmpSymbol.Kind != 'Const' and tmpSymbol.Kind != 'Sensor':
                    relyList.append(elem.value)