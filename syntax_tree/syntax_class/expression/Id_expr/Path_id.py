from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.Exceptions import *
from syntax_tree.syntax_class.syntaxSymbol import SyntaxConstSymbol, SyntaxSensorSymbol, SyntaxVariableSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxType
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Id_expr_Path_id(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        symbol = userOp.check_and_get_constant_param(self.name)
        if symbol is not None:
            self.set_rhs([])
        else:
            symbol = userOp.get_my_package().get_sensor_symbol(self.name)
            if symbol is None:
                symbol = userOp.get_localVariable_InThisAndPreEnv(self.name)
                if symbol is None:
                    raise UnknownIdentifierException(
                        self.name + " " + str(self) + f"在{userOp.get_global_name()}")  # 有枚举类型，可恶,把枚举类型给放到常数变量里了
                self.set_rhs([self.name])
            else:
                self.set_rhs(([]))
        self.set_symbol(symbol)
        self.allUsedSymbolNames={self.name}
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 要求只能提供一个左值类型，所以需要校验
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        required_type = lhs_type_list[0].get_real_type()
        symbol=self.syntaxSymbol
        expr_type = symbol.syntaxType.get_real_type()
        if expr_type <= required_type:
            self.set_lhs_type([expr_type])
        else:
            raise TypeMismatchException(f"{self}有type为{expr_type.get_real_type()}", required_type.get_real_type(),
                                        userOp)
        if isinstance(symbol,SyntaxConstSymbol) or isinstance(symbol,SyntaxSensorSymbol):
            self.set_clock_list([SyntaxClockExpr.init_clock_base(userOp)])
        else:
            self.set_clock_list([symbol.whenExpr])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        path_id = self.objects[0]  # 获取路径标识符，例如 "n"
        return syntaxUserOp.var_change_name(path_id)
    def generate_code_const(self,scope,genEqu):
        if self.lhsTypeList[0].is_basic_type():
            return f"{self.cal_const_value(SyntaxType('any'),scope).value}"
        else:
            return self.generate_code(scope,None)# 反正用不到
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.name=objects[0]
    def is_clock_expr(self):
        if self.syntaxSymbol is None:
            self.post_process(self.scope)
        if not isinstance(self.syntaxSymbol,SyntaxVariableSymbol):
            return False
        return self.syntaxSymbol.isClock
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        path_id = self.objects[0]
        scope = self.scope
        const_symbol = scope.check_and_get_constant_param(path_id)
        if not const_symbol or const_symbol.isImported:
            raise UnknownIdentifierException(path_id)
        return ConstValue(syntax_type=required_type, value=const_symbol.get_value())