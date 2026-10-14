from typing import Optional
from syntax_tree.syntax_class.Exceptions import *
from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
from syntax_tree.scade_postprocess import set_rhs_default
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Atom_bool_atom(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 要求只能提供一个左值类型，所以需要校验
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        syntax_type = SyntaxType('bool')
        if lhs_type_list[0].type=="any":
            self.set_lhs_type([syntax_type])
        elif lhs_type_list[0] <= syntax_type:
            self.set_lhs_type([lhs_type_list[0]])
        elif syntax_type <= lhs_type_list[0]:
            self.set_lhs_type([syntax_type])
        else:
            raise TypeMismatchException(f"{self}有type为{syntax_type}", lhs_type_list, userOp)
        self.set_clock_list([SyntaxClockExpr.init_clock_any(userOp)])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        return f"kcg_{self.objects[0]}"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        return ConstValue(syntax_type=self.lhsTypeList[0], value=f"kcg_{self.objects[0]}")
