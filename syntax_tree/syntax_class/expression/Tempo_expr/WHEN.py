import copy

from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from typing import TYPE_CHECKING
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Tempo_expr_WHEN(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum = self.objects[0].returnNum
        self.rhsList = add_rhs_to_each(self.objects[1].rhsList,copy.copy(self.objects[0].rhsList))
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        self.set_clock_list([self.objects[1]]*self.returnNum)
        result=self.objects[0].type_inference(lhs_type_list,userOp)
        self.set_lhs_type(result)
        return result
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):

        depth=genEqu.depth
        clock=self.lhsClockList[0]
        sub_code=self.objects[0].generate_code(syntaxUserOp, genEqu)
        if not isinstance(sub_code,list):
            sub_code=[sub_code]
        tmp_list=list()
        pre_code=f"{'    '*depth}if({clock.generate_code()}){{\n"
        for code,lhs_type in zip(sub_code,self.lhsTypeList):
            tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, self.lhsTypeList[0])
            tmp_list.append(tmp_name)
            pre_code+=f"{assign_lhs_to_rhs_expr(tmp_name,code,[lhs_type],depth+1,syntaxUserOp)}"
        pre_code+=f"{'    '*depth}}}\n"
        genEqu.add_preEquations(pre_code)
        return tmp_list if len(tmp_list)>1 else tmp_list[0]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

