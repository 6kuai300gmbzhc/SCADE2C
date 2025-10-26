from syntax_tree.scade_postprocess import flatten_list
from syntax_tree.scade_type_inference import type_inference_on_groups, clock_inference_sync
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import union_rhsLists
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from syntax_tree.syntax_class.syntaxType import SyntaxType
from typing import TYPE_CHECKING
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Tempo_expr_ARROW(SyntaxExpr):
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum = self.objects[0].returnNum
        self.rhsList = union_rhsLists([self.objects[0].rhsList, self.objects[1].rhsList])
    def type_inference(self, lhs_type_list: list['SyntaxType'], userOp:'SyntaxUserOp'):
        # arrow可以同时处理多个变量
        actual_types = type_inference_on_groups([self.objects[0], self.objects[1]], lhs_type_list, userOp)
        self.set_lhs_type(actual_types)
        self.set_clock_list(clock_inference_sync(flatten_list([expr.lhsClockList for expr in self.objects])))
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        init_var = syntaxUserOp.set_init_var()
        # 不能删，有提醒此句所在op有内存的功能
        # 因为scade和lustre在这里的语法规则不同，lustre认为如果没有执行到此句，则不更新init情况
        # 而scade则是无论如何都要更新
        # scade用下面这句
        # code_ = f"({syntaxUserOp.var_change_name(init_var.name)} ? ({self.objects[0].generate_code(syntaxUserOp, genEqu)}) : ({self.objects[1].generate_code(syntaxUserOp, genEqu)}))"

        # lustre中，为此句声明一个额外变量
        depth=genEqu.depth
        init_symbol,init_name=generate_tmp_symbol_and_register(syntaxUserOp, SyntaxType("bool"),"arrow_mem")
        init_symbol.isOutput=True
        tmp_name_list=list()
        for sub_type in self.lhsTypeList:
            tmp_symbol,tmp_name=generate_tmp_symbol_and_register(syntaxUserOp, sub_type)
            tmp_name_list.append(tmp_name)
        init_code=self.objects[0].generate_code(syntaxUserOp, genEqu)
        not_init_code=self.objects[1].generate_code(syntaxUserOp, genEqu)
        init_equation=assign_lhs_to_rhs_expr(tmp_name_list,init_code,self.lhsTypeList,depth+1,syntaxUserOp)
        not_init_equation=assign_lhs_to_rhs_expr(tmp_name_list,not_init_code,self.lhsTypeList,depth+1,syntaxUserOp)
        pre_code=f"{'    '*depth}if({syntaxUserOp.var_change_name(init_name)}){{\n" \
                 f"{init_equation}" \
                 f"{'    '*depth}}}else{{\n" \
                 f"{not_init_equation}" \
                 f"{'    '*depth}}}\n"
        pre_code+=f"{'    '*depth}{syntaxUserOp.var_change_name(init_name)}=kcg_false;\n"
        genEqu.add_preEquations(pre_code)
        # print("arrow set_init_var", len(syntaxUserOp.tmpParams), syntaxUserOp.name)
        # print("arrow set_init_var",syntaxUserOp.tmpParams)
        # for elem in syntaxUserOp.tmpParams:
        #     print("===", elem.name)
        return tmp_name_list[0] if len(tmp_name_list)==1 else tmp_name_list
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

