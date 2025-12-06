import typing
from abc import abstractmethod

from ..Exceptions import *
from typing import TYPE_CHECKING

from syntax_tree.exclude_from_deepcopy import exclude_from_deepcopy

if TYPE_CHECKING:
    from ..syntaxType import SyntaxTypeSymbol
    from .userOp import SyntaxUserOp
    from ..syntaxSymbol import SyntaxVariableSymbol, SyntaxConstSymbol
    from .package import SyntaxPackageScope


@exclude_from_deepcopy('prevScope')
class SyntaxScope:
    """作用域父类"""

    type: str
    '''为data_def,function,node,package,if_block,match_block,automaton,automaton_state'''
    name: str
    '''名字'''
    prevScope: 'SyntaxScope'
    '''父作用域'''
    childScopeTable: dict
    '''子作用域'''
    visibility: str = "public"
    '''可见性，默认为public'''
    anonymousScopeCount: int = 1
    '''匿名scope计数器，给匿名的block生成名字'''
    annoymousTmpCount: int = 0
    '''创建中间变量使用的init'''
    initSymbolSet: set['SyntaxVariableSymbol']
    '''其子作用域内的所有init变量集合,在userop范围内不能重名，userop以上为空集合'''
    tmpParams: list['SyntaxVariableSymbol']
    _hasInternalState: bool = False

    def __init__(self, type, name, prevScope, visibility):
        self.type = type
        self.name = name
        self.prevScope = prevScope
        self.visibility = visibility
        self.childScopeTable = dict()
        self.equations = list()
        self.initVar = None
        self.tmpParams = list()
        self.initSymbolSet = set()

    @property
    def hasInternalState(self) -> bool:
        '''该作用域内是否存在内存，例如control_block与一些时态算子等'''
        return self._hasInternalState or len(self.initSymbolSet) > 0

    @hasInternalState.setter
    def hasInternalState(self, value):
        self._hasInternalState = value

    def add_childScope(self, childScope: 'SyntaxScope') -> None:
        self.childScopeTable[childScope.name] = childScope

    def get_childScope(self, scopeName) -> 'SyntaxScope' or None:
        if scopeName in self.childScopeTable.keys():
            return self.childScopeTable[scopeName]
        else:
            return None

    def childScope2str(self, depth=0):
        if not self.childScopeTable: return ""
        s = ""
        s += "    " * depth + "childScope:\n"
        for _, scope in self.childScopeTable.items():
            s += scope.scope2str(depth=depth + 1)
        return s

    def generate_name_for_subScope(self):
        s = self.name
        s += "_subScope_"
        s += str(self.anonymousScopeCount)
        self.anonymousScopeCount += 1
        return s

    def get_global_name(self):
        if self.prevScope is None:  # 是global
            return "global"
        elif self.prevScope.name == "*global":
            if self.name == "switch":
                return f"_{self.name}"
            return self.name
        else:
            return self.name + "_" + self.prevScope.get_global_name()

    def add_tmpSymbol(self, tmpSymbol):
        self.tmpParams.append(tmpSymbol)

    def get_tmpSymbol(self, tmpSymbolName):
        for symbol in self.tmpParams:
            if symbol.name == tmpSymbolName: return symbol
        return None

    def get_localVariable_InThisAndPreEnv(self, name) -> 'SyntaxVariableSymbol' or None:
        if symbol := self.get_localVariable(name):
            return symbol
        return self.prevScope.get_localVariable_InThisAndPreEnv(name)

    def get_localVariable_InThisAndPreEnv_until_certain_scope(self,name,certain_scope):
        if certain_scope.prevScope is None or self is certain_scope.prevScope:
            return None
        if (symbol := self.get_localVariable(name)) is not None:
            return symbol
        return self.prevScope.get_localVariable_InThisAndPreEnv_until_certain_scope(name,certain_scope)

    def get_localVariable(self, name: str) -> 'SyntaxVariableSymbol' or None:
        for symbol in self.tmpParams:
            if name == symbol.name:
                return symbol
        return None

    def _get_certain_prev_scope(self, scope_types: typing.Iterable[str]):
        tar_scope = self
        while tar_scope is not None and tar_scope.type not in scope_types:
            tar_scope = tar_scope.prevScope
        return tar_scope

    def get_my_userOp(self):
        """返回此作用域对应的userOp作用域"""
        if self.type == "package": raise Exception(f"{self.name}是一个package")
        return self._get_certain_prev_scope({"function", "node"})

    def get_my_op_or_state(self):
        """返回此作用域对应的op或者状态机state的作用域，选取语法树上最近的那个"""
        if self.type == "package": raise Exception(f"{self.name}是一个package")
        return self._get_certain_prev_scope({"function", "node", "automaton_state"})

    def get_my_package(self) -> 'SyntaxPackageScope':
        return self._get_certain_prev_scope({"package"})

    def get_my_clocked_scope(self):
        return self._get_certain_prev_scope({"if_block", "match_block", "automaton"})

    def resolve_path(self, path_list: list):
        """解析Path类型，直接返回对应的package,输入数组格式,即split::后的"""
        cur_package: SyntaxPackageScope = self.get_my_package()
        # 先根据path第一个找到对应package，然后逐层向下找
        if len(path_list) == 0:
            return cur_package
        tar_package = cur_package.get_package_InThisAndPreEnv(path_list[0])
        if not tar_package:
            raise UnknownIdentifierException(f"找不到{path_list[0]}")
        for package_name in path_list[1:]:
            tar_package = tar_package.get_package(package_name)
            if not tar_package:
                raise UnknownIdentifierException(f"找不到{path_list[0]}")
        return tar_package

    def resolve_path_id(self, path_id: str) -> ('SyntaxPackageScope', str):
        """解析path_id，返回对应package和id"""
        path_id_list = path_id.split("::")
        if len(path_id_list) > 1:
            return self.resolve_path(path_id_list[:-1]), path_id_list[-1]
        else:
            return self.get_my_package(), path_id

    def check_and_get_userOp(self, path_id: str):
        """根据路径找到对应的userop，没有则返回None
         Parameters:
            path_id: 带::的路径，指向某个userop
        """
        target_package, op_name = self.resolve_path_id(path_id)
        return target_package.get_userOp(op_name)

    def check_and_get_constant_param(self, param_path_id):
        """检查这个参数是不是一个常数，如果是则返回syntaxconstSymbol，否则返回None
        """
        if self.type != "package":
            userOp = self.get_my_userOp()
            if (size_param := userOp.get_size_symbol(param_path_id)) is not None:
                return size_param
        tar_package, name = self.resolve_path_id(param_path_id)
        const_param = tar_package.get_const_symbol(name)
        return const_param

    def check_and_get_type_symbol(self, type_path_id) -> 'SyntaxTypeSymbol':
        """根据路径找到对应的type_decl，没有则返回None
         Parameters:
            type_path_id: 指向某个type_decl,可以没有：：
        """
        tar_package, name = self.resolve_path_id(type_path_id)
        return tar_package.get_type_symbol(name)

    def check_and_get_sensor_symbol(self,sensor_path_id)->'SyntaxSensorSymbol':
        tar_package, name = self.resolve_path_id(sensor_path_id)
        return tar_package.get_sensor_symbol(name)

    def get_const_symbol(self, symbol_name):
        raise Exception(f"{self.name} 作为{self.type}没有const")

    def get_type_symbol(self, type_name):
        return self.typeSymbolTable.get(type_name)

    def var_change_name(self, name):
        if name == "_": return name
        symbol = self.get_localVariable_InThisAndPreEnv(name)
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
                symbol = self.check_and_get_sensor_symbol(name)
            if symbol is None:
                raise ValueError(f"var_change_name error , name:{name}")
            return symbol.change_name()

    def scope2str(self) -> str:
        """一个抽象方法"""
        ...

    def generate_name_for_tmp(self, postfix="tmp", isOutPut=False):
        '''生成一个没有被用过的变量名，用来代码生成'''
        count = 0
        name = f"{postfix}"
        while self.get_localVariable_InThisAndPreEnv(name) is not None:
            count += 1
            name = f"{postfix}_{str(count)}"
        if isOutPut:
            name = self.get_my_userOp().generate_name_for_outC(name)
        return name
