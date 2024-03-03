# 1.使用一个符号表存储变量、函数、类型
# 2.使用符号表树实现作用域
from scade_compile_otherFunc import objectsToString
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
        self.StateType='' #ifBlock(变量赋值为if块),equation(变量赋值为等式),switchBlock,fbyBlock,structNormal

        self.Value = None  # 常量、变量等的值

        self.fbyList = list()

        self.FieldList = dict()  # 若该变量的Kind是Type，则为结构体变量名，和该名对应的symbol。
                                 #若该变量是结构体，则为结构体变量名，以及对应的类型
        self.FieldValueList = dict()  # 结构体变量的成员-默认值
        self.arrSize=list()  #数组长度的表达式
        self.arrValueList=list()
        self.relyList=list()

        self.initState = None  # 初始状态
        self.StrongOrWeak = None # 强迁移: 1, 弱迁移: 0
        self.StateList = list() # 状态机所有可能状态名列表
        self.Params = list()  # 函数标识符的参数列表
        self.Returns = list()  # 函数标识符的返回值列表
        self.Last=list() #变量的last属性列表
        self.Default=list() #变量的default属性列表
        self.Code = list()  # 变量对应的值

    def changeName(self):
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
        return name
    def symbolToString(self,subList,thisEnv):
        str=""
        if self.StateType=='equation':
            str+=self.Name
            str+=' = '
            str+=objectsToString(self.Code,thisEnv)
            str+=';\n'
        elif self.StateType=='ifBlock':
            for idx in range(len(self.Code)):
                if idx==0:
                    str+='if(%s){\n %s=%s;\n'%(objectsToString(self.Code[idx][0],thisEnv),self.Name,objectsToString(self.Code[idx][1],thisEnv))
                    if self.IsInit==True:
                        str+="%s = kcg_false;\n}"%(objectsToString(self.Code[0][0],thisEnv))
                    else:
                        str+="}\n"
                else:
                    if len(self.Code[idx][0])!=0:
                        str+="else if(%s){\n %s=%s;\n}"%(objectsToString(self.Code[idx][0],thisEnv),self.Name,objectsToString(self.Code[idx][1],thisEnv))
                    else:
                        str+="else{\n%s=%s;\n}\n"%(self.Name,objectsToString(self.Code[idx][1],thisEnv))
        elif self.StateType=='fbyBlock':
            str+="if(%s){\n for(int idx=0;idx<%s;idx++){\n"%(objectsToString(self.Code[0],thisEnv),objectsToString(self.Code[4],thisEnv))
            str+="%s[idx]=%s;\n}"%(objectsToString(self.Code[2],thisEnv),objectsToString(self.Code[5],thisEnv))
            str+="%s=0;\n"%(objectsToString(self.Code[1],thisEnv))
            if self.initState:
                str+="%s=kcg_false;\n}\n"%(objectsToString(self.Code[0],thisEnv))
            else:
                str+="}\n"
            str+="%s=%s[%s];\n"%(self.Name,objectsToString(self.Code[2],thisEnv),objectsToString(self.Code[1],thisEnv))
            str+="%s[%s]=%s;"%(objectsToString(self.Code[2],thisEnv),objectsToString(self.Code[1],thisEnv),objectsToString(self.Code[3],thisEnv))
            str+="%s=(%s+1)%%(%s);\n"%(objectsToString(self.Code[1],thisEnv),objectsToString(self.Code[1],thisEnv),objectsToString(self.Code[4],thisEnv))
        elif self.StateType=='switchBlock':
            str+="switch(%s){\n"%(objectsToString(self.Code[0],thisEnv))
            for idx in range(1,len(self.Code)):
                if len(self.Code[idx][0])!=0:
                    str+="case %s : \n %s = %s;\n break;\n"%(objectsToString(self.Code[idx][0],thisEnv),self.Name,objectsToString(self.Code[idx][1],thisEnv))
                elif len(self.Code[idx][0])==0 and len(self.Code[idx][1])!=0:
                    str+="default :\n %s=%s;\nbreak;\n"%(self.Name,objectsToString(self.Code[idx][1],thisEnv))
                else:
                    str+="default : \n break;\n"
            str+="}\n"
        return str


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
