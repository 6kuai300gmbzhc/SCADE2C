from typing import Optional
import copy

from syntax_tree.scade_type_inference import type_inference_on_groups, clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.scade_generate import GenEqu, assign_lhs_to_rhs_expr, generate_tmp_symbol_and_register
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_at(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 列表连接
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        required_type: SyntaxType = copy.copy(lhs_type_list[0])
        required_type.min_size = 0

        min_type = type_inference_on_groups(self.objects, [required_type], userOp)[0]
        first_type: SyntaxType = self.objects[0].lhsTypeList[0]
        second_type: SyntaxType = self.objects[1].lhsTypeList[0]
        size_sum=first_type.get_size() + second_type.get_size()
        if size_sum < required_type.min_size:
            raise TypeMismatchException(self, lhs_type_list, userOp)

        min_type.set_size(size_sum)
        self.set_clock_list(clock_inference_sync([expr.lhsClockList[0] for expr in self.objects]))
        self.set_lhs_type([min_type])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        # 列表连接
        array_type: SyntaxType = self.lhsTypeList[0]
        tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, array_type,"tmp_concat")
        depth = genEqu.depth
        tar_first_code = self.objects[0].generate_code(syntaxUserOp, genEqu)
        tar_second_code = self.objects[1].generate_code(syntaxUserOp, genEqu)
        first_size = self.objects[0].lhsTypeList[0].get_size()
        # 把这俩连一起
        pre_code = ""
        pre_code += assign_lhs_to_rhs_expr(tmp_name, tar_first_code, self.objects[0].lhsTypeList, depth, syntaxUserOp)
        pre_code += assign_lhs_to_rhs_expr(tmp_name + f"[{first_size}]", tar_second_code,
                                           self.objects[1].lhsTypeList,
                                           depth, syntaxUserOp)
        genEqu.add_preEquations(pre_code)
        return tmp_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

