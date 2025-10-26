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
class Relation_expr_Relation_expr(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.subExpr.post_process(userOp)
        set_rhs_default(self)
        self.subExpr.returnNum = sum([expr.returnNum for expr in self.objects[0]])
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # =与<>不对子类型做限制
        # 其他情况，则限制为numeric
        # 两侧的类型必须一致
        # 返回类型肯定是bool，不用讨论
        if len(lhs_type_list) != 1 and lhs_type_list[0] != SyntaxType('bool'):
            raise TypeMismatchException(self, lhs_type_list, userOp)

        op = self.objects[1]
        if op == "=" or op == "<>":
            required_type = SyntaxType("any")
        else:
            required_type = SyntaxType("numeric")
        type_inference_on_binop([required_type,required_type],userOp,self.subExpr,True)
        self.set_clock_list(clock_inference_sync(self.subExpr.lhsClockList))
        self.set_lhs_type([SyntaxType('bool')])
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        op = self.objects[1]
        sub_codes = self.subExpr.generate_code(syntaxUserOp, genEqu)
        ele_type=self.subExpr.lhsTypeList[0]
        if ele_type.is_basic_type() or ele_type.get_real_type().type=="enum":
            if op == '<>':
                op = '!='
            elif op == '=':
                op = '=='
            return f"({sub_codes[0]} {op} {sub_codes[1]})"
        # 如果是数组或结构体用memcpy
        if op=='<>':
            ans='1'
        elif op=="=":
            ans='0'
        else:
            raise Exception(f'{self.subExpr.lhsTypeList[0]}不支持{op}')
        code=f"memcmp((const void *) &{sub_codes[0]}, (const void *) &{sub_codes[1]}, sizeof({self.subExpr.lhsTypeList[0].change_name()}))=={ans}"
        return code
    def set_params(self,params:list['SyntaxExpr']):
        self.subExpr.objects[0]=[params[0],params[1]]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.subExpr=expression_factory("List_expr","List_expr",scope,[self.objects[0]])
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':...
