from syntax_tree.scade_type_inference import type_inference_on_binop, clock_inference_sync
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, expression_factory
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Bool_expr_binOp(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.subExpr.post_process(userOp)
        set_rhs_default(self)
        self.subExpr.returnNum = sum([expr.returnNum for expr in self.objects[0]])
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        """布尔运算，要求都是bool类型"""
        # 需求类型bool，子运算类型bool，很简单
        # packed_sub_expr = SyntaxExpr(type="List_expr", subtype="List_expr", scope=userOp,
        #                              objects=[self.objects[0], self.objects[2]], returnNum=2)
        required_type = SyntaxType("bool")
        if len(lhs_type_list) != 1 and lhs_type_list[0] != required_type:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        type_inference_on_binop([required_type, required_type], userOp, self.subExpr, False)
        self.set_lhs_type([required_type])
        self.set_clock_list(clock_inference_sync(self.subExpr.lhsClockList))
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        sub_codes = self.subExpr.generate_code(syntaxUserOp, genEqu)
        if self.objects[1]=="=>":
            return f"(!({sub_codes[0]}) | {sub_codes[1]})"
        else:
            op=SyntaxExpr.bool_binary_dict[self.objects[1]]
            return f"({sub_codes[0]} {op} {sub_codes[1]})"
    def set_params(self,params:list['SyntaxExpr']):
        self.subExpr.objects[0]=[params[0],params[1]]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.subExpr = expression_factory("List_expr", "List_expr", scope, [self.objects[0]])
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':...
