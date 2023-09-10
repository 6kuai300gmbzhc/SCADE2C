# 1.使用一个符号表存储变量、函数、类型
# 2.使用符号表树实现作用域

class Symbol:
    def __init__(self, Name=None, Kind=None, Type=None,Public=True,External=False,isPackage=False,PackageName='') -> None:
        self.Name = Name  # 标识符的名字
        self.Kind = Kind  # 标识符的类型：常量(Const) 变量(Var) 类型(Type) 节点(Node) 包(Package)

        self.Type = Type  # Type类型(int , float)
        self.Public=Public
        self.External=External

        self.IsPackage=isPackage
        self.PackageName=PackageName

        # self.VarType = VarType             #常量、变量等类型标识符的数据类型
        # self.TypeType = TypeType           #类型定义的基本类型，或者Struct、Enum
        # self.IsArray = IsArray
        # self.Size = Size                   #数组类型的大小
        # self.Clock = Clock                 #变量的时钟

        self.IsInput=False
        self.IsReturn = False

        self.Value = None  # 常量、变量等的值

        self.FieldList = dict()  # 结构体变量的成员-类型和枚举变量的名字-整数值
        self.FieldValueList = dict()  # 结构体变量的成员-默认值

        self.Params = list()  # 函数标识符的参数列表
        self.Returns = list()  # 函数标识符的返回值列表
        self.StaticParams = list()  # 函数的静态参数列表
        self.StaticArgs = list()
        self.Code = list()  # 函数标识符的代码

    def __repr__(self) -> str:
        strs = '#' + self.Name + '(' + self.Kind + ')'
        if self.Kind == 'Const':
            strs += '(' + repr(self.Type) + ':' + str(self.Value) + ')'
        elif self.Kind == 'Var':
            strs += '(' + repr(self.Type) + ')'
        elif self.Kind == 'Type':
            if self.Type:
                if self.Type.Type == 'Enum' or self.Type.Type == 'Struct':
                    strs += '(' + repr(self.Type) + ':' + str(self.FieldList) + ')'
                    if self.FieldValueList:
                        strs += '(' + str(self.FieldValueList) + ')'
                else:
                    if self.Type.Type:
                        strs += '(' + repr(self.Type) + ')'
        elif self.Kind == 'Node' or self.Kind == 'UndefineRed':
            strs += 'Params:' + str(self.Params) + 'Returns:' + str(self.Returns)
            if self.StaticParams:
                strs += 'StaticParams:' + str(self.StaticParams)
            strs += '\n'

        return strs


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
