from syntax_tree.syntax_class.Exceptions import TypeMismatchException, NumericConstraintViolateException
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, int_can_fit_type, float_can_fit_type
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Arith_expr_cast(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        set_rhs_default(self)
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        given_type = lhs_type_list[0]
        cast_type = self.objects[1]
        if not (cast_type <= SyntaxType("numeric") or cast_type != given_type):
            raise TypeMismatchException(self, lhs_type_list, userOp)
        self.set_lhs_type([cast_type])

        # 需要两边均为numeric,这边和输出没关系，只要是numeric就行，别的不管
        tar_expr = self.objects[0]
        tar_type = tar_expr.type_inference([SyntaxType("numeric")], userOp)[0]

        # 这里尝试计算一下表达式是否可以进行这样的转换
        try:
            value=tar_expr.cal_const_value(cast_type,userOp).value
            if cast_type<=SyntaxType("integer"):
                if not int_can_fit_type(value,cast_type.get_real_type().type):
                    raise NumericConstraintViolateException(value,cast_type)
            elif cast_type<=SyntaxType("float"):
                if not float_can_fit_type(value,cast_type.get_real_type().type):
                    raise NumericConstraintViolateException(value, cast_type)
        except Exception as e:
            if isinstance(e,NumericConstraintViolateException):
                raise e
        self.set_clock_list(tar_expr.lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        syntax_type = self.objects[1]
        expr = self.objects[0]
        return f"{(syntax_type.change_name_cast())}({expr.generate_code(syntaxUserOp, genEqu)})"
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        syntax_type = self.objects[1]
        const_value=self.objects[0].cal_const_value(required_type,scope)
        const_value.type=syntax_type
        return const_value

