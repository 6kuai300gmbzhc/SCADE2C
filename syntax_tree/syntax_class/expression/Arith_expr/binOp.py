from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.scade_type_inference import type_inference_on_binop
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, expression_factory
from typing import TYPE_CHECKING
from syntax_tree.syntax_class.syntaxType import SyntaxType
if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.scope.scope import SyntaxScope


class Arith_expr_binOp(SyntaxExpr):
    def post_process(self, userOp: 'SyntaxUserOp'):
        self.subExpr.post_process(userOp)
        set_rhs_default(self)
        self.subExpr.returnNum = sum([expr.returnNum for expr in self.objects[0]])
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp: 'SyntaxUserOp'):
        # binOp会根据不同的二元运算符给出不同的要求
        # lnot, land, lor, lxor 是两个unsigned，需求且输出unsigned
        # lsl ,lsr 第一个是unsigned，第二个是integer，需求且输出unsigned
        # 其他情况则与输入类型相同
        # 是最宽泛的类型需求，对非移位运算的情况，若子式发现可以更具体的话则要根据具体的类型再遍历一遍
        if len(lhs_type_list) != 1:
            raise TypeMismatchException(self, lhs_type_list, userOp)
        op = self.objects[1]
        given_type = lhs_type_list[0]
        required_given_type = SyntaxType("numeric")
        min_type = min([required_given_type, given_type])
        returned_type=type_inference_on_binop([min_type , min_type ], userOp, self.subExpr, False)[0]

        self.set_lhs_type([returned_type])
        self.set_clock_list(self.subExpr.lhsClockList)
        # 第一个子表达式，即左侧的那个表达式不管是什么操作符都是要返回的那个
        return self.lhsTypeList

    def generate_code(self, syntaxUserOp: 'SyntaxUserOp', genEqu: 'GenEqu'):
        op=SyntaxExpr.binop_dict[self.objects[1]]
        sub_codes=self.subExpr.generate_code(syntaxUserOp,genEqu)
        return f"({sub_codes[0]} {op} {sub_codes[1]})"
    def generate_code_const(self,scope,genEqu):
        return f"{self.cal_const_value(self.lhsTypeList[0],scope).value}"
    def set_params(self,params:list['SyntaxExpr']):

        self.subExpr.objects[0]=[params[0],params[1]]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.subExpr=expression_factory("List_expr","List_expr",scope,[self.objects[0]])
        ...

    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':
        value_left=self.objects[0][0].cal_const_value(required_type,scope).value
        value_right=self.objects[0][1].cal_const_value(required_type,scope).value
        binOP=self.objects[1]
        _value=eval(f"{str(value_left)}{SyntaxExpr.binop_dict[binOP]}{str(value_right)}")
        const_value=ConstValue(self.lhsTypeList[0],_value)
        return const_value
