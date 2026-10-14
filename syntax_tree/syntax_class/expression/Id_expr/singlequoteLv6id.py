from typing import Optional

from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException,TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Id_expr_singlequoteLv6id(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, data_def:'SyntaxUserOp'):
        name = self.name[1:]  # 去掉开头的'
        if not data_def.have_signal_InThisAndPreEnv(name):
            raise UnknownIdentifierException(name)
        # id_expr仅有单个返回值，设置rhs
        self.set_rhs([name])
        self.allUsedSymbolNames={self.name}
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 要求只能提供一个左值类型，所以需要校验
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        required_type = lhs_type_list[0]
        name = self.objects[0]
        expr_type = SyntaxType("bool")
        if expr_type <= required_type:
            self.set_lhs_type([expr_type])
        else:
            raise TypeMismatchException(f"{self}有type为{expr_type.get_real_type()}", required_type.get_real_type(),
                                        data_def)
        self.set_clock_list([SyntaxClockExpr.init_clock_any(data_def)])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        # 把signal的第一个字符也就是'去掉
        return self.name[1:]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.name=objects[0]
