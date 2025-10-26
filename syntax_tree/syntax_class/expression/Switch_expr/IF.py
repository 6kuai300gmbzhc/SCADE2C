import copy

from syntax_tree.scade_postprocess import flatten_list
from syntax_tree.scade_type_inference import type_inference_on_groups
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import union_rhsLists,add_rhs_to_each
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from typing import TYPE_CHECKING
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Switch_expr_IF(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum =int((self.objects[0].returnNum-1)/2)
        sub_rhs_list=self.objects[0].rhsList
        cond_rhs_list=[sub_rhs_list[0]]
        if_rhs_list=sub_rhs_list[1:1+self.returnNum]
        else_rhs_list=sub_rhs_list[1+self.returnNum:]
        # 将两个条件分支的因果关系逐个合并起来，然后加上条件语句的因果关系
        rhs_list = union_rhsLists([if_rhs_list, else_rhs_list])
        rhs_list = add_rhs_to_each(cond_rhs_list, rhs_list)
        self.rhsList = rhs_list
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        actual_types = self.objects[0].type_inference([SyntaxType("bool")]+lhs_type_list+lhs_type_list, userOp)
        if_lhs_list=actual_types[1:1+self.returnNum]
        else_lhs_list=actual_types[1+self.returnNum:]
        if if_lhs_list!=else_lhs_list:
            raise Exception("if语句两分支返回的类型不同")
        self.set_lhs_type(copy.copy(if_lhs_list))
        self.set_clock_list(flatten_list([expr.lhsClockList for expr in self.objects]))
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        if isinstance(self.objects[0],list):
            cond_code=self.objects[0][0].generate_code(syntaxUserOp, genEqu)
            code_1 = self.objects[0][1].generate_code(syntaxUserOp, genEqu)
            code_2 = self.objects[0][2].generate_code(syntaxUserOp, genEqu)
        else:
            code=self.objects[0].generate_code(syntaxUserOp,genEqu)
            cond_code=code[0]
            code_1=code[1:1+self.returnNum]
            code_2=code[1+self.returnNum:]
        if not isinstance(code_1,list):code_1=[code_1]
        if not isinstance(code_2,list):code_2=[code_2]
        out_code=list()
        for lhs_type,ele_1,ele_2 in zip(self.lhsTypeList,code_1,code_2):
            if lhs_type.get_real_type().type == "array":
                tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, lhs_type)
                depth=genEqu.depth
                pre_code=f"{'    '*depth}if({cond_code}){{\n" \
                         f"{assign_lhs_to_rhs_expr(tmp_name,ele_1,[lhs_type],depth+1,syntaxUserOp)}" \
                         f"{'    '*depth}}}else{{\n" \
                         f"{assign_lhs_to_rhs_expr(tmp_name,ele_2,[lhs_type],depth+1,syntaxUserOp)}" \
                         f"{'    '*depth}}}\n"
                genEqu.add_preEquations(pre_code)
                out_code.append(tmp_name)
            else:
                out_code.append(f"({cond_code} ? {ele_1} : {ele_2})")

        if self.returnNum==1:
            out_code =out_code[0]
        return out_code
    def set_params(self,params:list['SyntaxExpr']):
        self.objects[0]=[params[0],params[1],params[2]]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def cal_const_value(self,required_type:'SyntaxType',scope:'SyntaxScope') -> 'ConstValue':...
