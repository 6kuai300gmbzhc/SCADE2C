from typing import Optional
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_get(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        self.objects[1].type_inference([SyntaxType("integer")],userOp)
        idx_symbol = self.objects[1].cal_const_value(SyntaxType("integer"), userOp)
        # if idx_symbol.type!=SyntaxType("integer"):
        #     raise TypeMismatchException(self.objects[1], idx_symbol.type, userOp)
        required_type = lhs_type_list[0]
        idx_value = idx_symbol.value
        self.idx_list.append(idx_value)

        required_arr_type = SyntaxType("array", scope=userOp).set_element_and_size(required_type, 0)
        required_arr_type.min_size = idx_value
        given_arr_type: SyntaxType = self.objects[0].type_inference([required_arr_type], userOp)[0]
        self.set_lhs_type([given_arr_type.get_element_type_for_array()])
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        idx = self.idx_list[0]
        return f"{self.objects[0].generate_code(syntaxUserOp, genEqu)}[{idx}]"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

