# 1.使用一个符号表存储变量、函数、类型
# 2.使用符号表树实现作用域
class fbyClass:
    def __init__(self, idx='', arr=''):
        self.fbyIdx = idx
        self.fbyArr = arr
class Symbol:
    def __init__(self, Name='', Kind='', Type='',Public=True,External=False,isPackage=False,PackageName='',isStatemachine=False,StatemachineName='') -> None:
        self.Name = Name  # 标识符的名字
        self.Kind = Kind  # FbyIdx,FbyArr,Pre(重置函数中使用了),TmpVar,PathId
        #Type.structElem,OpKind,Sensor,State,Const,Var,Init

        self.Type = Type  # Type类型(int , float,enum,array,struct)
                            #Node还是function,struct
                            #起别名之后的类型名
        self.Public = Public
        self.External = External

        self.IsPackage = isPackage
        self.PackageName = PackageName
        self.isCalled=False   #用于标识一个node是否被调用

        self.isStatemachine=isStatemachine
        self.StateMachineName=StatemachineName

        # self.VarType = VarType             #常量、变量等类型标识符的数据类型
        # self.TypeType = TypeType           #类型定义的基本类型，或者Struct、Enum
        # self.Clock = Clock                 #变量的时钟

        self.IsInput = False
        self.IsReturn = False

        self.Value = None  # 常量、变量等的值

        self.fbyList = list()

        self.FieldList = dict()  # 结构体变量名，和该名对应的symbol
        self.FieldValueList = dict()  # 结构体变量的成员-默认值
        self.arrSize=list()  #数组长度的表达式

        self.initState = None  # 初始状态
        self.StrongOrWeak = None # 强迁移: 1, 弱迁移: 0
        self.StateList = list() # 状态机所有可能状态名列表
        self.Params = list()  # 函数标识符的参数列表
        self.Returns = list()  # 函数标识符的返回值列表
        self.Last=list() #变量的last属性列表
        self.Default=list() #变量的default属性列表
        self.Code = list()  # 函数标识符的代码

    def changeName(self,params):
        if self.IsInput==True:
            name="inC->"+self.Name
        elif self.IsReturn==True:
            name="outC->"+self.Name
        elif self.Kind=="PathId":
            name=self.Name
            for elem in self.Code:
                name+="_"+elem.value
            self.Code.clear()
        else:
            name=self.Name
        if len(params)!=0:
            for elem in params:
                name+=".%s"%elem.value
        return name
    #为类指定输出格式
    # def __repr__(self) -> str:
    #     strs = '#' + self.Name + '(' + self.Kind + ')'
    #     if self.Kind == 'Const':
    #         strs += '(' + repr(self.Type) + ':' + str(self.Value) + ')'
    #     elif self.Kind == 'Var':
    #         strs += '(' + repr(self.Type) + ')'
    #     elif self.Kind == 'Type':
    #         if self.Type:
    #             if self.Type.Type == 'Enum' or self.Type.Type == 'Struct':
    #                 strs += '(' + repr(self.Type) + ':' + str(self.FieldList) + ')'
    #                 if self.FieldValueList:
    #                     strs += '(' + str(self.FieldValueList) + ')'
    #             else:
    #                 if self.Type.Type:
    #                     strs += '(' + repr(self.Type) + ')'
    #     elif self.Kind == 'Node' or self.Kind == 'UndefineRed':
    #         strs += 'Params:' + str(self.Params) + 'Returns:' + str(self.Returns)
    #         if self.StaticParams:
    #             strs += 'StaticParams:' + str(self.StaticParams)
    #         strs += '\n'
    #
    #     return strs


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
        if self.SymbolTable:
            strs += str(self.SymbolTable)
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

    def getSymbolInThisEnv(self, name):
        symbol = None
        if self.SymbolTable.get(name):
            symbol = self.SymbolTable.get(name)
        return symbol

    def setSymbol(self, name, symbol):
        if not self.getSymbolInThisEnv(name):
            self.SymbolTable[name] = symbol
        else:
            print(name, 'symbol error')

    def popSymbol(self, name):
        symbol = None
        if self.SymbolTable.get(name):
            symbol = self.SymbolTable.pop(name)
        return symbol
