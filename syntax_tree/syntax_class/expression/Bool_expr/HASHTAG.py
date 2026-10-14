from typing import Optional
from syntax_tree.scade_postprocess import set_rhs_default, flatten_list
from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Bool_expr_HASHTAG(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, data_def:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        required_type = SyntaxType("bool")
        if len(lhs_type_list) != 1 and lhs_type_list[0] != required_type:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        sub_type = self.subType
        for sub_expr in self.objects[0]:
            sub_expr.type_inference([required_type], data_def)
        self.set_clock_list(clock_inference_sync(flatten_list([sub_expr.lhsClockList for sub_expr in self.objects[0]])))
        self.set_lhs_type([required_type])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        values = [obj.generate_code(syntaxUserOp, genEqu) for obj in self.objects[0]]
        constraints = [
            f"(!(({values[left]}) && ({values[right]})))"
            for left in range(len(values))
            for right in range(left + 1, len(values))
        ]
        return f"({' && '.join(constraints)})" if constraints else "kcg_true"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)