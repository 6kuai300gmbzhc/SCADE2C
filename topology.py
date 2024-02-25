class Topology:
    def __init__(self,name='',type=''):
        self.name=name
        self.type=type  #equation,ifBlock,switchBlock,fbyBlock,structNormal
        self.left=list()
        self.right=list()
        self.rely=list()
        self.condition=list() #ifBlock和fbyBlock中condition的格式不同
        #ifblock中[[[条件],[语句]],[[],[]]]。fbyBlock中为fby(expr1;num;expr2)[[initName],[fbyIdx],[fbyArr][expr1],[num],[expr2]]
        self.init=False


    def setRely(self,symbolTable):
        relyList=list()
        if self.type=='ifBlock':
            for elem in self.condition:
                relyList.extend(elem[0])
                relyList.extend(elem[1])
        elif self.type=='fbyBlock':
            for idx in range(2,len(self.condition)):
                relyList.extend(self.condition[idx])
        relyList.extend(self.right)
        for elem in relyList:
            if elem.strs=='lv6id':
                symbol=symbolTable.getSymbol(elem.value)
                if symbol!=None:
                    if symbol.IsInput!=True and symbol.Kind!='Const' and symbol.Kind!='Sensor':
                        self.rely.append(elem.value)
class Node:
    def __init__(self,name='',index=0,tpIdx=0,inNum=0,outNum=0):
        self.name=name
        self.index=index
        self.tpIdx=tpIdx
        self.inNum=inNum
        self.outNum=outNum
        self.finish=False

def topologySort(topologyObjs,adjList,nodeList):
    print("====topologySort",len(topologyObjs),len(nodeList))
    sum=len(nodeList)
    retList=[]
    for i in range(sum):
        if len(retList)>=sum:
            break
        for elem in nodeList:
            if len(retList)>=sum:
                break
            if elem.inNum==0 and elem.finish==False:
                print(elem.name)
                retList.append(topologyObjs[elem.tpIdx])
                elem.finish=True
                for j in range(len(adjList[elem.index])):
                    idx=adjList[elem.index][j]
                    nodeList[idx].inNum-=1
    return retList

def topologyReady(topologyObjs):
    adjList=[]
    nodeDict={}
    nodeList=[]
    num=0
    for idx in range(0,len(topologyObjs)):
        leftName=topologyObjs[idx].name
        if leftName not in nodeDict.keys():
            node=Node(leftName,num,idx)
            nodeList.append(node)
            nodeDict[leftName]=num
            num+=1
            adjList.append([])
        else:
            raise NotImplementedError('%s redefined'%leftName)
    for elem in topologyObjs:
        adjIdx1=nodeDict[elem.name]
        for relyElem in elem.rely:
            print(elem.name," rely on",relyElem)
            if relyElem not in nodeDict.keys():
                print(relyElem,"not in nodeDict")
            else:
                adjIdx2=nodeDict[relyElem]
                nodeList[adjIdx1].inNum+=1
                nodeList[adjIdx2].outNum+=1
                adjList[adjIdx2].append(adjIdx1)
    return topologySort(topologyObjs,adjList,nodeList)