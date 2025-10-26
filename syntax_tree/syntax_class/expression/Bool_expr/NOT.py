from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Bool_expr_NOT(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # 需求类型bool，子运算类型bool，很简单
        # packed_sub_expr = SyntaxExpr(type="List_expr", subtype="List_expr", scope=userOp,
        #                              objects=[self.objects[0], self.objects[2]], returnNum=2)
        required_type = SyntaxType("bool")
        if len(lhs_type_list) != 1 and lhs_type_list[0] != required_type:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        sub_type = self.subType
        self.objects[0].type_inference([required_type], userOp)
        self.set_lhs_type([required_type])
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def set_params(self,params:list['SyntaxExpr']):
        self.objects[0]=params[0]
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        return f"( !({self.objects[0].generate_code(syntaxUserOp, genEqu)}) )"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':...
