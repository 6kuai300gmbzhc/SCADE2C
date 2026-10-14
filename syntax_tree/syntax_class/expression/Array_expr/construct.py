from typing import Optional
from syntax_tree.syntax_class.Exceptions import TypeMismatchException, UnsatisfiableSizeException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_construct(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        required_type = lhs_type_list[0]
        given_element_type = self.objects[0].type_inference([required_type.get_element_type_for_array()], userOp)[
            0]
        self.objects[1].type_inference([SyntaxType("integer")],userOp)
        given_array_length = self.objects[1].cal_const_value(SyntaxType("integer"), userOp).value
        # 也有可能数组长度只有最小值限制
        if not (given_array_length == required_type.get_size() or given_array_length > required_type.min_size):
            raise UnsatisfiableSizeException(self, given_array_length,
                                             f"{required_type.get_size()}或最小值{required_type.min_size}")

        given_type = SyntaxType(tar_type="array", scope=userOp)
        given_type.set_element_and_size(given_element_type, given_array_length)
        self.set_lhs_type([given_type])
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        tmp_para, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, self.lhsTypeList[0], "array_tmp")
        size =self.objects[1].cal_const_value(SyntaxType("integer"), syntaxUserOp).value
        element = self.objects[0].generate_code(syntaxUserOp, genEqu)
        element_type=self.lhsTypeList[0].get_element_type_for_array()
        code = f"{'    ' * genEqu.depth}for(kcg_size idx{genEqu.depth}=0;idx{genEqu.depth}<{size};idx{genEqu.depth}++){{\n" \
               f"{assign_lhs_to_rhs_expr(f'{tmp_name}[idx{genEqu.depth}]',element,[element_type],genEqu.depth+1,syntaxUserOp)}" \
               f"{'    ' * genEqu.depth}}}\n"
        genEqu.add_preEquations(code)
        return tmp_name
    def generate_code_const(self,scope,genEqu):
        element=self.objects[0].generate_code_const(scope,genEqu)
        size = self.objects[1].cal_const_value(SyntaxType("integer"), scope).value
        code=f"{{{', '.join([element]*size)}}}"
        return code
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

