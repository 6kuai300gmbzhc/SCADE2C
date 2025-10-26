from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.scade_postprocess import set_rhs_default
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Arith_expr_unary(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        unary_op = self.objects[0]
        if unary_op=='lnot':
            if not lhs_type_list[0]<=SyntaxType("integer"):
                raise TypeMismatchException(self,"integer",userOp)
        tar_expr = self.objects[1]
        tar_type = tar_expr.type_inference(lhs_type_list, userOp)[0]
        self.set_lhs_type([tar_type])
        # 一元运算符，将目标类型传递下去，然后将实际类型返回，没有需要修改的地方
        self.set_clock_list(tar_expr.lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        unary_op = self.objects[0]
        if unary_op == '+':
            return f"{self.objects[1].generate_code(syntaxUserOp, genEqu)}"
        elif unary_op == '-':
            return f"-({self.objects[1].generate_code(syntaxUserOp, genEqu)})"
        else:  # lnot需要在中间层转化为lnot_uXX,先用uint64替代，等Expr的exprType得到可以将其替换
            if self.lhsTypeList[0]==SyntaxType('int32') or self.lhsTypeList[0]==SyntaxType('uint32'):
                return f"kcg_lnot_uint32({self.objects[1].generate_code(syntaxUserOp, genEqu)})"
            else:
                return f"kcg_lnot_uint64({self.objects[1].generate_code(syntaxUserOp, genEqu)})"

    def set_params(self,params:list['SyntaxExpr']):
        self.objects[1]=params[0]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        const_value = self.objects[1].cal_const_value(required_type, scope)
        const_value.value *=-1
        return const_value
