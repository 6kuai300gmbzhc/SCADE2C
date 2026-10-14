from typing import Optional
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register
from typing import TYPE_CHECKING
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_slice(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        self.objects[1].type_inference([SyntaxType("integer")], userOp)
        self.objects[2].type_inference([SyntaxType("integer")], userOp)
        idx_symbols = [self.objects[1].cal_const_value(SyntaxType("integer"), userOp),
                       self.objects[2].cal_const_value(SyntaxType("integer"), userOp)]
        for i, idx_symbol in enumerate(idx_symbols):
            # if idx_symbol.type!=SyntaxType("integer"):
            #     raise TypeMismatchException(expr.objects[i], idx_symbol.type, data_def)
            idx_value = idx_symbol.value
            self.idx_list.append(idx_value)

        required_arr_type = SyntaxType("array", scope=userOp).set_element_and_size(lhs_type_list[0], 0)
        required_arr_type.min_size = idx_symbols[1].value
        given_arr_type: SyntaxType = self.objects[0].type_inference([required_arr_type], userOp)[0]

        actual_returned_type = SyntaxType("array", scope=userOp).set_element_and_size(given_arr_type.arrayType,
                                                                                        idx_symbols[1].value
                                                                                        - idx_symbols[0].value + 1)
        self.set_lhs_type([actual_returned_type])
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        depth = genEqu.depth
        tmp_var, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, self.lhsTypeList[0])
        sliced_code = self.objects[0].generate_code(syntaxUserOp, genEqu)
        slice_type_name = self.lhsTypeList[0].change_name()

        genEqu.add_preEquations(
            f"{'    ' * depth}(void)kcg_assign_array(&({tmp_name}),  ({slice_type_name} *) &(({sliced_code})[{self.idx_list[0]}]), sizeof ({slice_type_name}));\n")
        return tmp_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

