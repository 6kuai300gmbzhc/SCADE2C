from syntax_tree.scade_postprocess import set_rhs_default, flatten_list
from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_getdefault(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 是一个动态取数的操作，所以不用静态获取下标
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        required_type = lhs_type_list[0]

        # 先校验一下下标部分的表达式
        idx_exprs = self.objects[1]
        required_arr_type = required_type
        for idx_expr in idx_exprs:
            idx_expr.type_inference([SyntaxType("integer")], data_def)
            # 逐层去构建一个给被取数表达式的对应类型
            # 对大小完全没要求，因为不知道到底是一个什么情况
            required_arr_type = SyntaxType("array", scope=data_def).set_element_and_size(required_arr_type, 0)
            required_arr_type.min_size = 0

        def get_element_type_recursive(arr_type: SyntaxType, depth):
            """递归获取元素类型"""
            cur_type = arr_type
            for i in range(depth):
                cur_type = cur_type.arrayType
            return cur_type

        def build_arr_type(element_type: SyntaxType, depth):
            """再根据元素类型填充成数组,对长度没有要求"""
            output: SyntaxType = element_type
            for i in range(depth):
                output = SyntaxType("array").set_element_and_size(output, 0)
                output.min_size = 0
            return output

        # 然后拿这个新得到的类型去推断被取数表达式
        given_arr_type = self.objects[0].type_inference([required_arr_type], data_def)[0]
        given_element_type = get_element_type_recursive(given_arr_type, len(idx_exprs))
        # 用提供的类型去推断默认表达式
        given_default_type = self.objects[2].type_inference([required_type], data_def)[0]

        if given_element_type < given_default_type:
            given_default_type = self.objects[2].type_inference([given_element_type], data_def)[0]
        elif given_default_type < given_element_type:
            given_arr_type = self.objects[0].type_inference([build_arr_type(given_default_type, len(idx_exprs))],
                                                 data_def)[0]
        self.set_clock_list(clock_inference_sync([expr.lhsClockList[0] for expr in flatten_list(self.objects)]))
        self.set_lhs_type([given_default_type])
        return self.lhsTypeList
    def generate_code(self, data_def:'SyntaxUserOp', genEqu:'GenEqu'):
        # 要在这里检查idx是不是超过数组长度了
        # 可以get很多层，所以需要递归的看数组
        depth = genEqu.depth
        tmp_var, tmp_name = generate_tmp_symbol_and_register(data_def, self.lhsTypeList[0])

        normal_expr: SyntaxExpr = self.objects[0]
        normal_code = normal_expr.generate_code(data_def, genEqu)
        arr_type = normal_expr.lhsTypeList[0]
        cur_type = arr_type
        cmp_code_list = []
        for idx_expr in self.objects[1]:
            idx_code = idx_expr.generate_code(data_def, genEqu)
            normal_code += f"[{idx_code}]"
            # 构建校验是否超出数组上限的表达式
            cur_size = cur_type.get_size()
            cur_type = cur_type.arrayType
            cmp_code_list.append(f"((kcg_lit_int32(0) <= {idx_code})&({idx_code} < kcg_lit_int32({cur_size})))")
        cmp_code = '&'.join(cmp_code_list)

        get_normal_code = assign_lhs_to_rhs_expr(tmp_name, normal_code, self.lhsTypeList, depth + 1, data_def)

        default_expr: SyntaxExpr = self.objects[2]
        default_code = default_expr.generate_code(data_def, genEqu)
        get_default_code = assign_lhs_to_rhs_expr(tmp_name, default_code, self.lhsTypeList, depth + 1, data_def)

        pre_code = f"{'    ' * depth}if({cmp_code}){{\n" \
                   f"{get_normal_code}" \
                   f"{'    ' * depth}}}\n" \
                   f"{'    ' * depth}else {{\n" \
                   f"{get_default_code}" \
                   f"{'    ' * depth}}}\n"
        genEqu.add_preEquations(pre_code)
        return tmp_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
