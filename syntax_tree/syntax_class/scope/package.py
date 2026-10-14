from typing import Optional
from .scope import SyntaxScope
from ..Exceptions import UnknownIdentifierException

from ..syntaxType import SyntaxTypeSymbol
from syntax_tree.exclude_from_deepcopy import exclude_from_deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .userOp import SyntaxUserOp


@exclude_from_deepcopy('prevScope')
class SyntaxPackageScope(SyntaxScope):
    """package对应scope，用于package和program
    包含子package，group，type，const，sensor与user_op声明
    program也算作package scope的一种，名字为 *global（防止重名）
    """
    type: str
    '''为package'''
    name: str
    '''名字'''
    prevScope: Optional['SyntaxPackageScope']
    '''父作用域'''
    childScopeTable: dict
    '''子作用域,这里只保存了子package'''

    typeSymbolTable: dict
    '''类型定义的符号表，类型名字->SyntaxTypeSymbol'''
    constSymbolTable: dict
    '''常量定义符号表，常量名字->SyntaxConstSymbol'''
    sensorSymbolTable: dict
    '''sensor定义符号表，sensor名字->SyntaxSensorSymbol'''
    groupSymbolTable: dict
    '''group定义符号表，group名字->SyntaxGroupSymbol'''
    userOpTable: dict
    '''函数，node的自定义符号表，因为path寻路只寻package所以独立出来，userop名字->SyntaxUserOpSymbol'''

    openPackageNames: list
    '''打开的其他package列表，存一个到目标package的路径，需要根据当前package的位置去寻找离他最近的那个'''
    openPackages: list["SyntaxPackageScope"]

    def __init__(self, type, name, prevscope, visibility):
        super().__init__(type, name, prevscope, visibility)
        self.typeSymbolTable = dict()
        self.constSymbolTable = dict()
        self.sensorSymbolTable = dict()
        self.groupSymbolTable = dict()
        self.userOpTable = dict()
        self.openPackageNames = list()
        self.openPackages = list()

    def scope2str(self, depth=0):
        s = "    " * depth
        s += "scope "
        prev_list = list()
        p = self.prevScope
        while p is not None:
            prev_list.append(p.name)
            p = p.prevScope
        for prev_scope in reversed(prev_list):
            s += prev_scope + "::"
        s += self.name + " as " + self.type
        s += ""
        s += "\n"
        depth = depth + 1
        if self.openPackageNames:
            s += "    " * depth + "open packages:\n"
            for package in self.openPackageNames:
                s += "    " * depth + "    " + package + "\n"
        if self.typeSymbolTable:
            s += "    " * depth + "typeSymbolTable:\n"
            for ID, symbol in self.typeSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.constSymbolTable:
            s += "    " * depth + "constSymbolTable:\n"
            for ID, symbol in self.constSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.sensorSymbolTable:
            s += "    " * depth + "sensorSymbolTable:\n"
            for ID, symbol in self.sensorSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.groupSymbolTable:
            s += "    " * depth + "groupSymbolTable:\n"
            for ID, symbol in self.groupSymbolTable.items():
                s += "    " * depth + "    " + ID + ":" + str(symbol) + "\n"
        if self.userOpTable:
            s += "    " * depth + "userOpTable:\n"
            for ID, symbol in self.userOpTable.items():
                s += symbol.scope2str(depth=depth + 1)
        if self.childScopeTable:
            s += "    " * depth + "childScope:\n"
            for _, scope in self.childScopeTable.items():
                if scope.type == "package": s += scope.scope2str(depth=depth + 1)
        return s

    def __repr__(self):
        return self.scope2str()

    def get_localVariable_InThisAndPreEnv(self, name) -> Optional['SyntaxVariableSymbol']:
        raise Exception(f"{self.get_global_name()}是package")

    def add_typeSymbol(self, typeSymbol: SyntaxTypeSymbol) -> None:
        self.typeSymbolTable[typeSymbol.name] = typeSymbol

    def add_constSymbol(self, constSymbol: 'SyntaxConstSymbol') -> None:
        self.constSymbolTable[constSymbol.name] = constSymbol

    def add_sensorSymbol(self, sensorSymbol: 'SyntaxSensorSymbol') -> None:
        self.sensorSymbolTable[sensorSymbol.name] = sensorSymbol

    def add_groupSymbol(self, groupSymbol: 'SyntaxGroupSymbol') -> None:
        self.groupSymbolTable[groupSymbol.name] = groupSymbol

    def add_userOp(self, userOp: 'SyntaxUserOp') -> None:
        self.userOpTable[userOp.name] = userOp
        # self.childScopeTable[userOp.name]=userOp

    def add_open_package(self, path) -> None:
        if path not in self.openPackageNames:
            self.openPackageNames.append(path)

    def var_change_name(self, name):
        # generate_id_expr_path_id函数中syntaxUserOp可能为UserOp，此时需要添加inC，outC，可能是package，为了防止package情况下，没有var_change_name。
        return name

    def get_package(self, package_name):
        return self.childScopeTable.get(package_name)

    def get_package_InThisAndPreEnv(self, package_name):
        tar_package = self.get_package(package_name)
        if tar_package: return tar_package
        if self.is_global(): return None
        return self.prevScope.get_package_InThisAndPreEnv(package_name)

    def is_global(self):
        return self.name == "*global"

    def open_packages(self):
        """打开对应package，将各种symbol复制到此处"""
        for package_name in self.openPackageNames:
            package = self.resolve_path(package_name.split("::"))
            if package is None:
                raise UnknownIdentifierException(package_name)
            else:
                print(f"{self.name}打开了{package.name}")
                self.openPackages.append(package)
        # self.typeSymbolTable |= tar_package.typeSymbolTable
        # self.constSymbolTable |= tar_package.constSymbolTable
        # self.sensorSymbolTable |= tar_package.sensorSymbolTable
        # self.groupSymbolTable |= tar_package.groupSymbolTable

    def get_const_symbol(self, symbol_name):
        symbol = self._get_symbol_all_reachable_scope("constSymbolTable", symbol_name)
        if symbol is not None:
            symbol.used = True
        return symbol

    def get_type_symbol(self, type_name):
        return self._get_symbol_all_reachable_scope("typeSymbolTable", type_name)

    def get_sensor_symbol(self,sensor_name):
        return self._get_symbol_all_reachable_scope("sensorSymbolTable",sensor_name)

    def get_userOp(self, userOp_name):
        return self._get_symbol_all_reachable_scope("userOpTable", userOp_name)

    def _get_symbol_all_reachable_scope(self, table_name, symbol_name):
        """真正的找symbol方法，找自己的下层package, 上层package，和自己"""
        reachable_scope = [self] + list(self.childScopeTable.values())
        prev_package = self.prevScope
        while prev_package is not None:
            reachable_scope.append(prev_package)
            prev_package = prev_package.prevScope
        for scope in reachable_scope:
            if symbol := scope.get_symbol_self_and_open_scope(table_name, symbol_name):
                return symbol
        return None

    def get_symbol_self_and_open_scope(self, table_name, symbol_name):
        """找自己的，与open的"""
        packages = [self] + self.openPackages
        for package in packages:
            symbol = self._get_symbol_by_dynamic_call(package, table_name, symbol_name)
            if symbol is not None:
                return symbol
        return None

    @staticmethod
    def _get_symbol_by_dynamic_call(package, table_name, symbol_name):
        tar_table: dict = getattr(package, table_name, None)
        if tar_table is None:
            raise Exception(f"没有这个表 {table_name} 这不对吧")
        return tar_table.get(symbol_name)
