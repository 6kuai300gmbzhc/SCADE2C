from syntax_tree.syntax_class.expression import SyntaxExpr

from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class generalized_get(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.rhsList=self.objects[0].rhsList
        self.returnNum=self.objects[0].returnNum
        # self.returnNum=
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        """给iterator等表达式使用，要求expr为数组，对其进行抽象的取数操作，即int[]变为int，可以对多返回值也生效"""
        # 组建对下层表达式需要的左值类型,获取lhs作为数组元素的类型
        self.objects[1].type_inference([SyntaxType("integer")],userOp)
        sub_lhs_list = []
        array_size = self.objects[1].cal_const_value(SyntaxType("int32"),userOp).value
        map_index = self.objects[2]
        if map_index < 0 or map_index > len(lhs_type_list):
            raise Exception(f"不对，{map_index}>{lhs_type_list}的长度了")
        for i in range(len(lhs_type_list)):
            lhs = lhs_type_list[i]
            if i < map_index:
                sub_lhs_list.append(lhs)
            else:
                sub_lhs = SyntaxType(tar_type="array", scope=userOp)
                sub_lhs.set_element_and_size(lhs, array_size)
                sub_lhs_list.append(sub_lhs)

        actual_type_list:list[SyntaxType] = self.objects[0].type_inference(sub_lhs_list, userOp)
        for i in range(map_index,len(lhs_type_list)):
            actual_type_list[i]=actual_type_list[i].get_element_type_for_array()
        self.set_lhs_type(actual_type_list)
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp, genEqu):
        raise Exception("不应该执行到这里,需要用set_params替换参数")
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
