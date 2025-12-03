from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from typing import TYPE_CHECKING
from syntax_tree.syntax_class.syntaxType import SyntaxType


if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_reverse(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 列表反向
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        actual_type = self.objects[0].type_inference(lhs_type_list, data_def)
        self.set_lhs_type(actual_type)
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def generate_code(self, data_def:'SyntaxUserOp', genEqu:'GenEqu'):
        array_type: SyntaxType = self.lhsTypeList[0]
        tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, array_type)
        idx_symbol, idx_name = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
        depth = genEqu.depth
        src_code = self.objects[0].generate_code(data_def, genEqu)
        pre_code = ""
        pre_code += f"{'    ' * depth}for ({idx_name} = 0; {idx_name} < {array_type.get_size()}; {idx_name}++) {{\n" \
                    f"{assign_lhs_to_rhs_expr(f'{tmp_name}[{idx_name}]', f'{src_code}[{array_type.get_size() - 1}-{idx_name}]', [array_type.get_element_type_for_array()], depth + 1, data_def)}" \
                    f"{'    ' * depth}}}\n"
        genEqu.add_preEquations(pre_code)
        return tmp_name
    def generate_code_const(self,scope,genEqu):
        pass
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        pass
