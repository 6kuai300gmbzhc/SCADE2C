from syntax_tree.scade_postprocess import set_rhs_default, flatten_list
from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.scade_generate import GenEqu, assign_lhs_to_rhs_expr, generate_tmp_symbol_and_register
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxSymbol import SyntaxConstSymbol
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Mixed_constructor_Mixed_constructor(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 复制构造函数，然后允许修改
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, data_def)
        tar_type = lhs_type_list[0].get_real_type()
        self.objects[0].type_inference(lhs_type_list, data_def)

        cur_type = tar_type
        sync_clock_list=list(self.objects[0].lhsClockList)
        for idx in self.objects[1]:
            if isinstance(idx, str) and cur_type.type == "field_decl":
                tar_symbol: SyntaxConstSymbol = cur_type.get_element_for_fields(idx)
                if tar_symbol is None:
                    TypeMismatchException(idx, "取数方式错误", data_def)
                cur_type = tar_symbol.syntaxType
                # 结构体取数
            elif isinstance(idx, SyntaxExpr) and cur_type.type == "array":
                idx.type_inference([SyntaxType("integer")], data_def)
                cur_type = cur_type.get_element_type_for_array()
                sync_clock_list.append(idx.lhsClockList)
                # 数组取数
            else:
                raise TypeMismatchException(idx, "取数方式错误", data_def)
        # 确认这个type是右值type
        self.objects[2].type_inference([cur_type], data_def)
        sync_clock_list.append(self.objects[2].lhsClockList)
        self.set_clock_list(clock_inference_sync(flatten_list(sync_clock_list)))
        self.set_lhs_type(lhs_type_list)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        # 先copy，然后修改
        struct_type = self.lhsTypeList[0]
        tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, struct_type, "tmp_mix")

        depth = genEqu.depth

        pre_code = ""
        pre_code += assign_lhs_to_rhs_expr(tmp_name, self.objects[0].generate_code(syntaxUserOp, genEqu),
                                           self.lhsTypeList, depth, syntaxUserOp)
        lhs_name = tmp_name
        for idx in self.objects[1]:
            # 拼一下下标和取数部分
            if isinstance(idx, str):
                lhs_name += "." + idx
            elif isinstance(idx, SyntaxExpr):
                lhs_name += f"[{idx.cal_const_value(SyntaxType('integer'), syntaxUserOp).value}]"
        pre_code += assign_lhs_to_rhs_expr(lhs_name, self.objects[2].generate_code(syntaxUserOp, genEqu),
                                           self.objects[2].lhsTypeList, depth, syntaxUserOp)
        genEqu.add_preEquations(pre_code)
        return tmp_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
