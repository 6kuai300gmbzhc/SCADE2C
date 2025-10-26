import copy

from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_transpose(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 列表转置
        first_dim = int(self.objects[1])
        second_dim = int(self.objects[2])
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        tar_type = copy.copy(lhs_type_list[0])
        cur_type = tar_type
        max_dim = max(first_dim, second_dim)
        min_dim = min(first_dim, second_dim)

        # 构造新type，交换指定数组下标的维度尺寸
        tmp_size = None
        tmp_type = None
        for i in range(1, max_dim + 1):
            if i == min_dim:
                tmp_size = cur_type.get_size()
                tmp_type = cur_type
            elif i == max_dim:
                tmp_type.set_size(cur_type.get_size())
                cur_type.set_size(tmp_size)
            if i != max_dim and not cur_type.type == "array":
                raise Exception(f"{data_def.get_global_name()}中的{self}，转置下标超过数组维度")
            cur_type = cur_type.get_element_type_for_array()
        actual_type = self.objects[0].type_inference([tar_type], data_def)
        self.set_lhs_type(actual_type)
        return self.lhsTypeList
    def generate_code(self, data_def:'SyntaxUserOp', genEqu:'GenEqu'):
        src_code = self.objects[0].generate_code(data_def, genEqu)
        dst_symbol, dst_name = generate_tmp_symbol_and_register(data_def, self.lhsTypeList[0])

        src_type = self.objects[0].lhsTypeList[0]
        max_idx = max(self.objects[1], self.objects[2])
        min_idx = min(self.objects[1], self.objects[2])

        depth = genEqu.depth
        idx_names = list()

        # 深度为max的for循环去构建下标
        def generate_pre_code_recursive(cur_depth, cur_type: SyntaxType, idx_count) -> str:
            idx_symbol, idx_name = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
            idx_names.append(idx_name)
            cur_code = ""
            cur_code += f"{'    ' * cur_depth}for ({idx_name} = 0; {idx_name} < {cur_type.get_size()}; {idx_name}++) {{\n"
            if idx_count != max_idx:
                cur_code += f"{generate_pre_code_recursive(cur_depth + 1, cur_type.get_element_type_for_array(), idx_count + 1)}"
            else:
                # 等于max的时候停止递归，输出outC->o3[idx2][idx1][idx] = inC->i3[idx][idx1][idx2];这样的句子来进行具体的操作
                idx_codes = [f"[{idx_name}]" for idx_name in idx_names]
                src = src_code + "".join(idx_codes)
                idx_codes[min_idx - 1], idx_codes[max_idx - 1] = idx_codes[max_idx - 1], idx_codes[min_idx - 1]
                dst = dst_name + "".join(idx_codes)
                cur_code += assign_lhs_to_rhs_expr(dst, src, [cur_type], cur_depth, data_def)
            cur_code += f"{'    ' * cur_depth}}}\n"
            return cur_code

        pre_code = generate_pre_code_recursive(depth, src_type, 1)
        genEqu.add_preEquations(pre_code)
        return dst_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
