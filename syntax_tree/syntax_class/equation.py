from abc import abstractmethod,ABC
from functools import cache
from typing import TYPE_CHECKING

from .Exceptions import UnknownIdentifierException
from .expression.clock_expr import SyntaxClockExpr
from .hasRhs import HasRhs
from .scope.userOp import SyntaxUserOp

from .syntaxType import SyntaxType

if TYPE_CHECKING:
    from .expression.expr_common import SyntaxExpr
    from .graph import Vertex
    from .scope.package import SyntaxPackageScope
    from .syntaxSymbol import SyntaxVariableSymbol

class LeftItem(ABC):
    type:str
    '''左值类型，为id,field,select,slice'''
    scope: SyntaxUserOp
    '''所处作用域'''
    def __init__(self,_type,scope):
        self.type=_type
        self.scope=scope
        self.__syntaxType=None


    # @property
    # def value(self) -> str:
    #     return self.symbol_name
    # @value.setter
    # def value(self, new_value: str):
    #     if not isinstance(new_value, str):
    #         raise TypeError("symbol_name must be a string")
    #     self.symbol_name = new_value
    # 让对象可哈希，且与字符串哈希一致
    # def __hash__(self):
    #     return hash(self.symbol_name)
    # 让对象与字符串、自身比较时都按 symbol_name 比较
    def __eq__(self, other):
        if isinstance(other, LeftItem):
            return self.type == other.type and self.scope is other.scope and self.symbol_name==other.symbol_name
        if isinstance(other, str):
            return self.symbol_name == other
        return NotImplemented

    @property
    @abstractmethod
    def symbol_name(self):
        '''获取左值'''
        ...
    @abstractmethod
    def change_name(self)->str:
        ...
    @abstractmethod
    def type_inference(self)->SyntaxType:
        '''对左值的类型推导，找不到就报错'''
        ...
    @abstractmethod
    def get_clock(self):
        '''确定左值的时钟表达式'''
        ...
class LeftItemId(LeftItem):
    name:str
    def __init__(self,scope,name):
        super().__init__("id",scope)
        self.name=name
    def __repr__(self):
        return self.symbol_name
    def change_name(self):
        return self.scope.var_change_name(self.symbol_name)
    @property
    def symbol_name(self):
        return self.name
    def type_inference(self)->SyntaxType:
        if self.symbol_name=="_":
            return SyntaxType("any")
        lhs_symbol = self.scope.get_localVariable_InThisAndPreEnv(self.symbol_name)
        if not lhs_symbol:
            raise UnknownIdentifierException(self)
        return lhs_symbol.syntaxType
    def get_clock(self):
        if self.symbol_name=="_":
            return SyntaxClockExpr.init_clock_base(self.scope)
        lhs_symbol = self.scope.get_localVariable_InThisAndPreEnv(self.symbol_name)
        if not lhs_symbol:
            raise UnknownIdentifierException(self)
        return lhs_symbol.whenExpr
class SyntaxEquation(HasRhs):
    """保存一句scade的equation，用来排序和生成代码，包含左值和右值"""
    type: str
    '''euqaion的类型，包括simple_equation，assume，guarantee，emission，control_block'''
    expr: 'SyntaxExpr' = None
    '''右值，
    对simple_equation为Syntaxexpr
    对assert为Syntaxexpr
    对emission为Syntaxexpr,无条件emit会填一个为true的expr
    对control_block为None
    '''
    controlBlockID: str
    '''仅type为control_block时有效，保存了对应block的名字
    没有填名字的block会自动给他们生成一个名字，确保能够搜索到
    这个block的具体内容会存放在当前作用域的子作用域列表里面
    '''
    assertID: str
    '''仅类型为assume，guarantee生效，保存带比较的ID名称
    assert语句不会改变这个ID的取值，所以不是左值
    '''
    emit: bool = True
    '''在状态机里的状态转移语句里，有可能在一句emission前没有emit关键词
    这个成员变量记录了这种情况，具体作用还不清楚
    对于其他情况则完全没有作用'''
    lineno: int
    '''此语句在原文中的行号
    如果为-1则是遍历时加上去的
    '''
    lhs: list[LeftItem]
    '''左值列表，可以由0-多个ID组成
    对simple_equation来说就是左值
    对assert来说是一个_即忽略左值
    '''
    lhs2RhsDict: dict[str:set]
    '''存储lhs到rhs列表的字典，说实话有点冗余了，但是也没办法就这样吧'''
    vertex: 'Vertex' = None
    '''这个句子所对应的图节点'''

    scope: 'SyntaxUserOp'
    '''这个句子所属于的作用域'''

    def __init__(self, type: str,scope:SyntaxUserOp, lhs: list[LeftItem]=None, lineno: int = -1):
        super().__init__()
        self.type = type
        self.scope=scope
        if self.type=="assert":
            self.lhs = [LeftItemId(scope,"_")]
        else:
            self.lhs=lhs
        self.lineno = lineno
        self.lhs2RhsDict = dict()

    def set_expr(self, expr: 'SyntaxExpr'):
        self.expr = expr

    def set_vertex(self, vertex):
        self.vertex = vertex

    def set_scope(self, scope: 'SyntaxDataDefScope'):
        self.scope = scope

    def equation2str(self, depth=0):
        s = "    " * depth + "行号" + ": " + str(self.lineno) + " "
        if self.type == "assume" or self.type == "guarantee":
            s += self.type + " " + self.assertID + " : " + str(self.expr)
            return s
        if self.type == "emission": s += "emit "
        s += " lhs:"
        s += "("
        if len(self.lhs) > 0:
            if self.lhsTypeList:
                s += ",".join(
                    [f"{str(self.lhs[index])} as {self.lhsTypeList[index].get_real_type().type}" for index in
                     range(len(self.lhs))])
            else:
                s += ",".join([f"{str(self.lhs[index])}" for index in range(len(self.lhs))])
        else:
            s += " "
        s += ")"
        if self.type == "emission":
            if self.expr:
                s += " if " + str(self.expr)
            return s
        s += " = "
        if self.type != "control_block":
            if self.expr: s += str(self.expr)
        else:
            s += self.controlBlockID

        return s

    def dependent_on_param_directly(self, param_name) -> bool:
        """这个句子是否直接依赖于这个变量？输入变量名称"""
        for ls in self.rhsList:
            if param_name in ls: return True
        return False

    def dependent_on_equation_directly_and_get_correspond_lhs(self, tar_equation) -> str or None:
        """判断自己是否直接依赖tar，即检测自己的右值是否和tar的左值重合,如果依赖的话则返回对应的lhs，否则返回None"""
        for lhs in tar_equation.lhs:
            if self.dependent_on_param_directly(lhs.symbol_name): return lhs
        return None

    def get_dependent_equations(self) -> list:
        """这个句子所依赖的全部句子"""
        return [vertex.value for vertex in self.vertex.get_all_from_vertexes()]

    def get_rhs_list_by_name(self, lhs: str):
        """找到这个句子中，lhs所对应的rhs列表，没有则为None"""
        return self.lhs2RhsDict.get(lhs)

    def __repr__(self):
        return self.equation2str()