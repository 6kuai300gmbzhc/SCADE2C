from syntax_tree.graph import Graph
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException

from syntax_tree.syntax_class.scope.package import SyntaxPackageScope
from syntax_tree.syntax_class.scope.scope import SyntaxScope
from syntax_tree.syntax_class.syntaxSymbol import SyntaxVariableSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.syntax_class.equation import SyntaxEquation

class SyntaxDataDefScope(SyntaxScope):  # 在data_def下，只有状态机和clocked_block直接作为他的子作用域了
    """data_def对应scope，用于user_op，control_block中的scope
    包含signal和local声明部分
    """
    type: str
    '''为data_def'''
    name: str
    '''名字'''
    prevScope: SyntaxScope
    '''父作用域，指向一个package'''
    childScopeTable: dict
    '''子作用域'''

    visibility: str = "public"
    '''可见性，默认为public'''
    equations: list
    '''该作用域中的scade语句，在data_def下的作用域才有语句，上层的作用域（package）只有声明'''
    signalSymbolSet: set
    '''存放signal类型，保存signal的ID集合,signal的ID没有‘，只有ID本身的部分'''
    localSymbolTable: dict
    '''存放局部变量，变量名字->SyntaxVariableSymbol,signal不属于这个集合'''
    returnSymbolsTable: dict
    '''存放了当前及下级作用域修改的，外部作用域的变量，变量名字->SyntaxVariableSymbol'''
    initVar: SyntaxVariableSymbol
    '''时态算子使用的init,每个作用域只有一个init'''
    equationDependentGraph: Graph
    """标识语句依赖关系的单向图"""
    lhs2EquationDict: dict
    """左值名字找对应句子的dict，没有signal！！"""

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.signalSymbolSet = set()
        self.localSymbolTable = dict()
        self.returnSymbolsTable = dict()
        self.equationDependentGraph = Graph()
        self.lhs2EquationDict = dict()

    @property
    def hasInternalState(self) -> bool:
        '''该作用域内是否存在内存，例如control_block与一些时态算子等'''
        return super().hasInternalState or self.initVar is not None

    def is_param_declared_externally(self, param_name):
        """判断这个变量是不是在此作用域的外部定义的"""
        # 当前作用域找不到这个变量，但是上面的作用域找到了，说明是一个要返回的变量
        symbol = self.get_localVariable(param_name)
        if symbol is None:
            symbol = self.get_localVariable_InThisAndPreEnv(param_name)
        else:
            return False
        if symbol is None:
            raise UnknownIdentifierException(f"{param_name} in {self.get_global_name()}")
        else:
            return True

    def add_equation(self, input_equation: 'SyntaxEquation'):
        # 直接放进去，遍历完所有语句之后再进行排序
        # 还有各种设置索引和句子所属作用域
        self.equations.append(input_equation)
        self.equationDependentGraph.addVertex(input_equation)
        input_equation.set_scope(self)
        # 更新返回列表
        for lhs in input_equation.lhs:
            lhs_name=lhs.symbol_name
            if lhs_name == "_": return

            if input_equation.type == "emission":
                # 信号部分单独处理一下,找不到就报错
                if not self.have_signal_InThisAndPreEnv(lhs_name):
                    raise UnknownIdentifierException(lhs_name + " in " + str(input_equation))
            if self.is_param_declared_externally(lhs_name):
                self.returnSymbolsTable[lhs_name] = self.get_localVariable_InThisAndPreEnv(lhs_name)
            if self.lhs2EquationDict.get(lhs_name) is None:
                self.lhs2EquationDict[lhs_name] = [input_equation]
            else:
                self.lhs2EquationDict[lhs_name].append(input_equation)
    def get_equation_by_lhs(self, lhs_name):
        return self.lhs2EquationDict.get(lhs_name)

    def get_localVariable(self, name: str) -> SyntaxVariableSymbol or None:
        '''在当前作用域找局部变量'''
        if name not in self.localSymbolTable.keys():
            return self.get_tmpSymbol(name)
        else:
            return self.localSymbolTable[name]

    def get_localVariable_InThisAndPreEnv(self, name: str) -> SyntaxVariableSymbol or None:
        '''递归的找局部变量'''
        local_symbol = self.get_localVariable(name)
        if local_symbol is None:
            return self.prevScope.get_localVariable_InThisAndPreEnv(name)
        else:
            return local_symbol

    def have_signal_InThisAndPreEnv(self, name: str) -> bool:
        '''递归的校验有没有这个signal'''
        if self.type == "function" or self.type == "node":
            # 上层不可能有signal了，不再往上层寻找
            return name in self.signalSymbolSet
        # 上层还能接着找
        if name in self.signalSymbolSet:
            return True
        else:
            if not isinstance(self.prevScope, SyntaxDataDefScope):
                # 上层是automaton或者control_block就跳过这一层
                return self.prevScope.prevScope.have_signal_InThisAndPreEnv(name)
            return self.prevScope.have_signal_InThisAndPreEnv(name)

    def generate_name_for_tmp(self, postfix="tmp"):
        '''生成一个没有被用过的变量名，用来代码生成'''
        count = 0
        name = f"{postfix}"
        while self.get_localVariable_InThisAndPreEnv(name) is not None:
            count += 1
            name = f"{postfix}_{str(count)}"
        return name

    def generate_name_for_init(self, postfix="init"):
        count = 0
        name = f"{postfix}"
        init_names = [symbol.name for symbol in self.get_my_userOp().initSymbolSet]
        while self.get_localVariable_InThisAndPreEnv(name) is not None or name in init_names:
            count += 1
            name = f"{postfix}_{str(count)}"
        return name

    def set_init_var(self):
        if self.initVar is None:
            init_name = self.generate_name_for_init()
            self.initVar = SyntaxVariableSymbol(init_name,self)
            self.initVar.isOutput = True
            self.initVar.syntaxType = SyntaxType("bool")
            self.add_tmpSymbol(self.initVar)
            cur_scope = self.prevScope
            # 逐层向上添加进入initSymbolSet
            while True:
                if isinstance(cur_scope, SyntaxPackageScope):
                    break
                cur_scope.initSymbolSet.add(self.initVar)
                cur_scope = cur_scope.prevScope
        return self.initVar

    def var_change_name(self, name):
        if name == "_": return name
        symbol = self.get_localVariable_InThisAndPreEnv(name)
        if symbol is None:
            symbol = self.get_tmpSymbol(name)
        if symbol is not None:
            if symbol.isOutput:
                return f"outC->{symbol.name}"
            elif symbol.isInput:
                return f"inC->{symbol.name}"
            else:
                return symbol.name
        else:
            symbol = self.check_and_get_constant_param(name)
            if symbol is None:
                raise ValueError(f"var_change_name error , name:{name}")
            return symbol.change_name()

    def get_return_symbolTable(self):
        '''获取此作用域修改的上层作用域中的变量，不包括信号，path_id是只读的不用管他'''
        return self.returnSymbolsTable

    def set_signalSymbolList(self, signalSymbolList: list):
        self.signalSymbolSet = set(signalSymbolList)

    def add_localSymbol(self, localSymbol):
        self.localSymbolTable[localSymbol.name] = localSymbol

    def scope2str(self, depth=0):
        s = "    " * depth
        s += "" + self.type + " as "
        prev_list = list()
        p = self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p = p.prevScope
        for prev_scope in reversed(prev_list):
            s += prev_scope + "::"
        s += self.name
        if self.hasInternalState:
            s += " initVar as "
            s += self.initVar.name + " "
        s += ""
        s += "\n"
        s += self.signalSymbolSet2str(depth=depth)
        s += self.localSymbolTable2str(depth=depth)
        s += self.childScope2str(depth=depth)
        s += self.equations2str(depth=depth)
        return s

    def signalSymbolSet2str(self, depth=0):
        if not self.signalSymbolSet: return ""
        s = ""
        s += "    " * depth + "signalSymbolSet:\n"
        if len(self.signalSymbolSet) > 0:
            s += "    " * depth + "    "
            for ID in self.signalSymbolSet:
                s += ID + ","
            s = s[:-1]
            s += "\n"
        return s

    def localSymbolTable2str(self, depth=0):
        if not self.localSymbolTable: return ""
        s = ""
        s += "    " * depth + "localSymbolTable:\n"
        for ID, symbol in self.localSymbolTable.items():
            s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        return s

    def equations2str(self, depth=0):
        if not self.equations: return ""
        s = ""
        s += "    " * depth + "equations:\n"
        for equation in self.equations:
            s += equation.equation2str(depth=depth + 1) + "\n"
        return s