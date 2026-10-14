from syntax_tree.scade_type_inference import type_inference_on_groups, clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException, UnsatisfiableSizeException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default, flatten_list
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import  generate_tmp_symbol_and_register,assign_lhs_to_rhs_expr
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Array_expr_list(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 构造函数，允许output:int32^4;然后output=[(1,2),(3,4)];实在是太抽象了
        # 还好准备了returnNum属性用来处理list的情况
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        required_type = lhs_type_list[0]
        elements: list[SyntaxExpr] = self.objects[0].objects[0]
        return_sum = sum([element.returnNum for element in elements])
        if not (required_type.get_size() == return_sum or required_type.min_size < return_sum):
            UnsatisfiableSizeException(self, required_type.get_size(),
                                       f"{required_type.get_size()}或最小值{required_type.min_size}")

        # 然后把子类型都分发下去
        # 为什么我之前不这么做？？？？太愚蠢了，明明直接把list_expr拆开就好了
        # 不过无需考虑list_expr的嵌套格式还是不错的
        element_exprs = list()
        for element in elements:
            if element.type == "List_expr":
                element_exprs.extend(element.objects)
            else:
                element_exprs.append(element)
        actual_element_type = \
            type_inference_on_groups(element_exprs, [required_type.get_element_type_for_array()], userOp)[0]
        self.set_lhs_type(
            [SyntaxType("array", scope=userOp).set_element_and_size(actual_element_type, return_sum)])
        self.set_clock_list(clock_inference_sync(flatten_list([expr.lhsClockList for expr in element_exprs])))
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        # 数组初始化函数，直接写成{a,b,c,d}即可
        elements: list[SyntaxExpr] = self.objects[0].objects[0]
        base_type=self.lhsTypeList[0].get_element_type_for_array()
        sub_codes=[expr.generate_code(syntaxUserOp, genEqu) for expr in elements]
        tmp_symbol,tmp_name=generate_tmp_symbol_and_register(syntaxUserOp,self.lhsTypeList[0],"tmp_list")
        for i,sub_code in enumerate(sub_codes):
            genEqu.add_preEquations(
                assign_lhs_to_rhs_expr(f"{tmp_name}[{i}]",sub_code,[base_type],genEqu.depth,syntaxUserOp)
            )
        return tmp_name
    def generate_code_const(self,scope,genEqu):
        elements: list[SyntaxExpr] = self.objects[0].objects[0]
        sub_codes=[expr.generate_code_const(scope, genEqu) for expr in elements]
        return f"{{{', '.join(sub_codes)}}}"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

