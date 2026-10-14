from typing import Optional
import copy

from .data_def import SyntaxDataDefScope
from ..graph import Graph
from ..Exceptions import *
from typing import TYPE_CHECKING
from .scope import SyntaxScope
from syntax_tree.exclude_from_deepcopy import exclude_from_deepcopy
from ..syntaxSymbol import SyntaxVariableSymbol, SyntaxConstSymbol
from ..syntaxType import SyntaxType,SyntaxTypeSymbol

if TYPE_CHECKING:
    from ..equation import SyntaxEquation
    from .package import SyntaxPackageScope
    from ..expression.expr_common import SyntaxExpr

@exclude_from_deepcopy('prevScope','dependentFunctions','instantiatedOpList')
class SyntaxUserOp(SyntaxDataDefScope):
    """
    包含slocal声明部分
    记录func或者node，作为一种scope存在
    被调用时的名字为他的global_name
    """
    type: str
    '''分为function和node两种'''
    name: str
    '''名字'''
    prevScope: 'SyntaxPackageScope'
    '''父作用域，指向一个package'''
    childScopeTable: dict
    '''子作用域'''
    equations: list
    '''该作用域中的scade语句'''
    visibility: str = "public"
    '''可见性，默认为public'''
    isImported: bool
    '''是不是imported'''
    sizeParams: list['SyntaxConstSymbol']
    '''输入的size参数，其中每个值都是const,需要实例化后才有实际意义'''
    inParams: list  # 存SyntaxVariableSymbol
    '''输入参数，是一个变量声明列表'''
    outParams: list  # 存SyntaxVariableSymbol
    '''输出参数，是一个变量声明列表'''
    # tmpParams: list # 存SyntaxVariableSymbol
    # '''中间参数，是一个变量声明列表'''
    numericKind: str = None
    '''如果是模板方法则填入对应类型，不是则为None'''
    typeVarSymbolTable: dict[str:SyntaxTypeSymbol]
    '''声明的模板类型,使用类型变量来记录模板类型，方便查找与替换'''
    specDecl: str = None
    '''声明的SPECIALIZE类型，存放一个pathID，没有声明则为None'''
    dependentFunctions: list
    '''此函数依赖的其他函数的路径列表'''
    apply_exprs: list['SyntaxExpr']
    '''记录了这个op下所有函数调用的情况，用来给代码生成环节添加outC
    '''
    output2inputDependents: list[list[int]]
    '''记录此函数中，输出参数对输入参数的因果关系,二维数组，依次给output记录其依赖的input的列表，均为对应数组下标
    注意，在此userop没有返回值的时候，也会存在依赖关系，就好像存在一个默认的返回值一样。
    所以要注意区分，不能依靠这个表来判断函数的返回值情况，只有outParams才行
    '''
    outCNameSet: set[str]
    '''
    存储了需要加入outC的东西的名字，用于避免各种重名情况
    只做名字的管理工作
    '''
    instantiatedOpList:list['SyntaxUserOp']
    '''
    存储了此op通过实例化产生的op，用于产生最终的遍历顺序
    '''
    opReturnSymbolCache:dict[str:[str,[str]]]
    '''
    若调用的函数输入为空且有内存，则他们会把结果缓存起来
    用调用函数的get_outC_name方法作为key
    value中第一个元素存储了对应函数注册的outC_name
    第二个元素存储了输出的那堆代码
    '''
    def __init__(self, type, name, prevscope, visibility="public", isImported=False):
        super().__init__(type, name, prevscope, visibility)
        self.inParams = list()
        self.outParams = list()
        self.typeVarSymbolTable = dict()
        # self.tmpParams = list()
        self.sizeParams = list()
        self.dependentFunctions = list()
        self.output2inputDependents = list()
        self.isImported = isImported
        self.apply_exprs = list()
        self.outCNameSet = set()
        self.instantiatedOpList=list()
        self.opReturnSymbolCache=dict()

    def add_instantiatedOp(self,op):
        self.instantiatedOpList.append(op)
    @property
    def hasInternalState(self) -> bool:
        return super().hasInternalState or any(expr.get_applied_op().hasInternalState for expr in self.apply_exprs)
    @hasInternalState.setter
    def hasInternalState(self,value):
        self._hasInternalState=value
    def set_sizeDecl(self, sizeDecl: list):
        # 所有的sizeDecl都是正整数，但是得设置成int类型，我觉得有问题，但是这就是残酷的现实
        for name in sizeDecl:
            const_symbol = SyntaxConstSymbol(name=name, scope=self)
            const_symbol.syntaxType = SyntaxType(tar_type="integer")
            self.sizeParams.append(const_symbol)

    def get_size_symbol(self, name):
        for symbol in self.sizeParams:
            if symbol.name == name:
                return symbol
        return None
    def add_apply_expr(self,expr):
        self.apply_exprs.append(expr)
    def set_outParams(self, outParams):
        self.outParams = outParams
        if not self.outParams:
            self.output2inputDependents.append([])
            return
        for para in self.outParams:
            para.isOutput = True
            self.output2inputDependents.append([])
    def set_inParams(self, inParams:list['SyntaxVariableSymbol']):
        self.inParams=inParams
        for para in self.inParams:
            para.isInput=True

    def get_localVariable(self, name: str) -> Optional['SyntaxVariableSymbol']:
        '''在当前作用域找局部变量，包括输入输出参数'''
        if name not in self.localSymbolTable.keys():
            for symbol in self.inParams:
                if name == symbol.name:
                    return symbol
            for symbol in self.outParams:
                if name == symbol.name:
                    return symbol
            for symbol in self.tmpParams:
                if name == symbol.name:
                    return symbol
            return None
        else:
            return self.localSymbolTable[name]

    def get_localVariable_InThisAndPreEnv(self, name: str) -> Optional['SyntaxVariableSymbol']:
        '''递归的找局部变量，包括输入输出参数'''
        return self.get_localVariable(name)  # 上层不可能有变量了

    def add_dependent_function(self, path):
        if path in self.dependentFunctions: return
        self.dependentFunctions.append(path)

    def add_input_output_dependency(self, input_index, output_index):
        """在这两个输入/输出参数之间建立因果关系"""
        if input_index in self.output2inputDependents[output_index]: return
        self.output2inputDependents[output_index].append(input_index)

    def isTemplate(self):
        return self.numericKind is not None or len(self.sizeParams) > 0

    def add_type_var(self, type_var_name):
        self.typeVarSymbolTable[type_var_name] = \
            SyntaxTypeSymbol(name=type_var_name, syntaxType=SyntaxType(self.numericKind))

    def get_type_var_symbol(self, type_var_name):
        return self.typeVarSymbolTable.get(type_var_name)

    def get_inC_name(self):
        return f"inC_{self.get_global_name()}"

    def get_outC_name(self):
        return f"outC_{self.get_global_name()}"

    def register_outC_name(self,name)->None:
        """向outC中注册一个不重名的名字"""
        if name in self.outCNameSet:
            raise Exception(f"{name}已经在{self.get_global_name()}中出现了")
        self.outCNameSet.add(name)
    def generate_name_for_outC(self,prefix)->str:
        '''生成一个在outC结构体中不重名的名字'''
        if prefix not in self.outCNameSet:
            return prefix
        count=1
        while True:
            name=f"{prefix}_{str(count)}"
            if name not in self.outCNameSet:
                return name
            count+=1
    def generate_name_for_outC_and_register(self,prefix):
        name=self.generate_name_for_outC(prefix)
        self.register_outC_name(name)
        return name

    def scope2str(self, depth=0):
        s = "    " * depth
        s += ""
        if self.isImported:
            s += " imported "
        s += "userOpScope as " + self.type + " "
        prev_list = list()
        p = self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p = p.prevScope
        for prev_scope in reversed(prev_list):
            s += prev_scope + "::"
        s += self.name
        s += "( "
        for inParam in self.inParams:
            s += str(inParam) + ","
        s = s[:-1]
        s += ")"
        s += " returns ( "
        for outParam in self.outParams:
            s += str(outParam) + ","
        s = s[:-1]
        s += ")"
        if self.numericKind:
            s += " where "
            for decl in self.typeVarSymbolTable.keys():
                s += decl + ","
            s = s[:-1]
            s += " is " + self.numericKind
        if self.specDecl:
            s += " specialize " + self.specDecl
        s += ""
        s += "\n"
        s += self.signalSymbolSet2str(depth=depth + 1)
        s += self.localSymbolTable2str(depth=depth + 1)
        s += self.equations2str(depth=depth + 1)
        s += self.childScope2str(depth=depth + 1)
        return s

    def __repr__(self):
        return self.scope2str()


