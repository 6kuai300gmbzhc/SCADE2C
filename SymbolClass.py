# 1.使用一个符号表存储变量、函数、类型
# 2.使用符号表树实现作用域
class fbyClass:
    def __init__(self, idx='', arr=''):
        self.fbyIdx = idx
        self.fbyArr = arr
class Symbol:
    def __init__(self, Name='', Kind='', Type='',Public=True,External=False,isPackage=False,PackageName='',isStatemachine=False,StatemachineName='') -> None:
        self.Name = Name  # 标识符的名字
        self.Kind = Kind  # FbyIdx,FbyArr,Pre(重置函数中使用了),TmpVar
        #Type.structElem,OpKind,Sensor,State,Const,Var,Init,ApplyOp,ApplyOut
        #Global,Package,OpKind,IfBlock,Size,Sig

        self.Type = Type  # Type类型(int , float,enum,array,struct)
                            #Node还是function,struct
                            #起别名之后的类型名
        self.Public = Public
        self.External = External
        self.hasInternalState = False

        self.IsPackage = isPackage
        self.PackageName = PackageName
        self.isCalled = False   #用于标识一个node是否被调用
        self.isPathId = False

        self.isStatemachine = isStatemachine
        self.StateMachineName = StatemachineName

        # self.VarType = VarType             #常量、变量等类型标识符的数据类型
        # self.TypeType = TypeType           #类型定义的基本类型，或者Struct、Enum
        # self.Clock = Clock                 #变量的时钟
        self.isTemplate = False
        self.templateTypeDict = dict()
        self.templateTypeList = list()

        self.IsInput = False
        self.IsReturn = False
        self.StateType = '' #ifBlock(变量赋值为if块),equation(变量赋值为等式),switchBlock,fbyBlock,structNormal,ApplyExpr
        self.IsLast = False #若变量有last，且在node中有被使用到last，才会初始化为last的值

        self.Value = None  # 常量、变量等的值

        self.fbyList = list()

        self.FieldList = dict()  # 若该变量的Kind是Type，则为结构体变量名，和该名对应的symbol。
        self.FieldValueList = dict()  # 结构体变量的成员-默认值
        self.arrSize = list()  #数组长度的表达式
        self.arrValueList = list()
        self.relyList = list()
        self.pathList = list()

        self.initState = None  # 初始状态
        self.StrongOrWeak = None # 强迁移: 1, 弱迁移: 0
        self.StateList = list() # 状态机所有可能状态名列表
        self.Params = list()  # 函数标识符的参数列表
        self.Returns = list()  # 函数标识符的返回值列表。不包括在转换过程中生成的中间的返回变量。
        self.Last = list() #变量的last属性列表
        self.Default = list() #变量的default属性列表
        self.Code = list()  # 变量对应的值
        self.callOperators = list() # 该函数所调用的函数名称列表，可用于在C文件中添加相应的宏定义引用

    def changeName(self,thisEnv):
        if self.IsInput==True:
            name="inC->"+self.Name
        elif self.IsReturn==True:
            name="outC->"+self.Name
        elif self.isPathId==True:
            name=self.Name
            for elem in self.Code:
                name+="_"+elem.value
            self.Code.clear()
        else:
            name=self.Name+self.PackageName
        return name

    def __str__(self):
        return str(self.Code)


class SymbolTable:
    def __init__(self, EnvName=None, PrevTable=None) -> None:
        self.EnvName = EnvName
        self.SymbolTable = dict()
        self.PrevTable = PrevTable
        self.ChildTableList = list()

    def SymbolTable2Str(self, layer=0):
        tab = ''
        for i in range(layer):
            tab += '  '
        strs = tab + 'Symbol_Table:' + self.EnvName
        strs+="{"
        if self.SymbolTable:
            for key in self.SymbolTable.keys():
                strs += key+":"
                strs += str(self.SymbolTable.get(key))
                strs += " "
        strs += "}"
        strs += '\n'
        if self.ChildTableList:
            for chiletable in self.ChildTableList:
                strs += chiletable.SymbolTable2Str(layer + 1)
        return strs

    def getSymbol(self, name):
        symbol = None
        if self.SymbolTable.get(name):
            symbol = self.SymbolTable.get(name)
        elif self.PrevTable:
            symbol = self.PrevTable.getSymbol(name)
        return symbol
    
    def getSymbolInThisAndPreEnv(self, name):
        symbol = None
        tmp = self
        while tmp:
            if tmp.SymbolTable.get(name):
                symbol = tmp.SymbolTable.get(name)
                break
            tmp = tmp.PrevTable
        return symbol

    def getSymbolInThisEnv(self, name):
        symbol = None
        if self.SymbolTable.get(name):
            symbol = self.SymbolTable.get(name)
        return symbol

    def setSymbol(self, name, symbol):
        if not self.getSymbolInThisEnv(name):
            self.SymbolTable[name] = symbol
        else:
            print(name, 'symbol error ! Env.Name=',self.EnvName)
            # print(self.printSymbol())

    def popSymbol(self, name):
        symbol = None
        if self.SymbolTable.get(name):
            symbol = self.SymbolTable.pop(name)
        return symbol

    def getSymbolTable(self,name):
        for table in self.ChildTableList:
            if table.EnvName==name:
                return table

    def printSymbol(self):
        print("=======EnvName",self.EnvName)
        for name,symbol in self.SymbolTable.items():
            print("name=",name,symbol.Name," kind=",symbol.Kind," type=",symbol.Type," IsInput",symbol.IsInput," packageName=",symbol.PackageName," isTemplate=",symbol.isTemplate,len(symbol.Code)," relyList=",symbol.relyList)
        print("=======End")

    def printChildTable(self):
        print("=====ChildTableList")
        for elem in self.ChildTableList:
            print(elem.EnvName)
        print("======End")
    
    def printPath(self):
        print("=======getPath======",self.EnvName)
        prev=self.PrevTable
        while prev!=None and prev.EnvName != 'Global':
            print("prevTable.EnvName=",prev.EnvName)
            prev=prev.PrevTable
        print("=====================")

    def __str__(self):
        return self.SymbolTable2Str(0)