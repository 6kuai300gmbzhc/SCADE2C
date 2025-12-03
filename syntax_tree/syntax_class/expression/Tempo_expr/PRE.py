from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr

from typing import TYPE_CHECKING
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr

if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.syntaxType import SyntaxType
    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Tempo_expr_PRE(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum = self.objects[0].returnNum
        self.rhsList=[set()]*self.returnNum
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        self.set_lhs_type(self.objects[0].type_inference(lhs_type_list, userOp))
        self.set_clock_list(self.objects[0].lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        syntaxUserOp.hasInternalState=True
        codes=self.objects[0].generate_code(syntaxUserOp, genEqu)
        if not isinstance(codes,list):
            codes=[codes]
        tmp_name_list=[]
        for post_code,lhs_type in zip(codes,self.lhsTypeList):
            tmp_var, tmp_var_name = generate_tmp_symbol_and_register(syntaxUserOp, self.lhsTypeList[0],"pre_mem",isOutPut=True)
            real_name=syntaxUserOp.var_change_name(tmp_var_name)
            tmp_name_list.append(real_name)
            tmp_var.postExpr = f"{assign_lhs_to_rhs_expr(real_name,post_code,[lhs_type],0,syntaxUserOp)}"
        return tmp_name_list if self.returnNum>1 else tmp_name_list[0]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

