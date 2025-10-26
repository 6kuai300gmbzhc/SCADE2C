from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Struct_expr_get(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        sub_type = self.subType
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        tar_type = lhs_type_list[0]
        # 结构体取数，没办法从这里知道具体是那个结构体，用any推理
        struct_type: SyntaxType = self.objects[0].type_inference([SyntaxType("any")], userOp)[
            0].get_real_type()
        if struct_type.get_real_type().type != "field_decl":
            raise TypeMismatchException(f"{self.objects[0]}应该是结构体", str(struct_type), userOp)
        ele_name = self.objects[1]
        tar_symbol = struct_type.get_element_for_fields(ele_name)
        if tar_symbol is None or not tar_symbol.syntaxType <= tar_type:
            raise Exception(f"{userOp.get_global_name}中的{self},无法从结构体中取{ele_name}元素")
        self.set_lhs_type([tar_symbol.syntaxType])
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
        # 没有return，说明没找到
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        struct = self.objects[0].generate_code(syntaxUserOp, genEqu)
        return f"{struct}.{self.objects[1]}"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

