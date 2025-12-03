from syntax_tree.scade_postprocess import flatten_list
from syntax_tree.scade_type_inference import type_inference_on_groups, clock_inference_sync
from syntax_tree.syntax_class.expression.expr_common import SyntaxExpr, expression_factory
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register
from typing import TYPE_CHECKING
if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
from .ARROW import Tempo_expr_ARROW
class Tempo_expr_FBY(SyntaxExpr):
    equivalent_expr:Tempo_expr_ARROW
    def post_process(self,data_def:'SyntaxUserOp'):
        self.rhsList=self.objects[2].rhsList
        self.returnNum = self.objects[0].returnNum
        # # 这里加一个优化，如果fby(a;1;b)则转为b->pre a
        # if self.objects[1].cal_const_value(SyntaxType("integer"),data_def).value==1:
        #     pre_sub_expr=expression_factory("List_expr","List_expr",data_def,
        #                             objects=[[SyntaxExpr("Tempo_expr","PRE",data_def,[self.objects[0]])]])
        #     pre_sub_expr.post_process(data_def)
        #     self.subType="ARROW"
        #     self.objects=[self.objects[2],pre_sub_expr]
        # # 这里加一个优化，转为b->pre a
        # pre_sub_expr = expression_factory("List_expr", "List_expr", userOp,
        #                           objects=[[expression_factory("Tempo_expr", "PRE", userOp, [self.objects[2]])]])
        # self.equivalent_expr= Tempo_expr_ARROW("Tempo_expr","ARROW",self.scope,[self.objects[0], pre_sub_expr],self.objects[2].returnNum)
        # self.rhsList=self.objects[0].rhsList
        # self.returnNum=self.equivalent_expr.returnNum

    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 和pre预算非常的相似
        actual_types = type_inference_on_groups([self.objects[0], self.objects[2]], lhs_type_list, data_def)
        self.set_lhs_type(actual_types)
        self.set_clock_list(clock_inference_sync(flatten_list([self.objects[0].lhsClockList,self.objects[2].lhsClockList])))
        return self.lhsTypeList
        # result=self.equivalent_expr.type_inference(lhs_type_list,userOp)
        # self.set_clock_list(self.equivalent_expr.lhsClockList)
        # self.set_lhs_type(result)
        # return result
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        idxVar, tmp_idx_var_name = generate_tmp_symbol_and_register(syntaxUserOp, SyntaxType("int32"), "idx",isOutPut=True)

        arrSyntaxType = SyntaxType("array",syntaxUserOp)
        arrSyntaxType.sizeExpr = self.objects[1]
        arrSyntaxType.arrayType = self.lhsTypeList[0]

        arrVar, tmp_arr_var_name = generate_tmp_symbol_and_register(syntaxUserOp, arrSyntaxType, "arr",isOutPut=True)

        initVar = syntaxUserOp.set_init_var()

        depth = genEqu.depth
        preCode = f"{'    ' * depth}if({syntaxUserOp.var_change_name(initVar.name)}){{\n" \
                  f"{'    ' * (depth + 1)}for(int idx=0;idx<{arrSyntaxType.get_size()};idx++){{\n" \
                  f"{'    ' * (depth + 2)}{syntaxUserOp.var_change_name(tmp_arr_var_name)}[idx] = {self.objects[2].generate_code(syntaxUserOp, genEqu)};\n" \
                  f"{'    ' * (depth + 1)}}}\n" \
                  f"{'    ' * (depth + 1)}{syntaxUserOp.var_change_name(tmp_idx_var_name)} = 0;\n" \
                  f"{'    ' * depth}}}\n"
        postCode = [
            f"{syntaxUserOp.var_change_name(tmp_arr_var_name)}[{syntaxUserOp.var_change_name(tmp_idx_var_name)}]={self.objects[0].generate_code(syntaxUserOp, genEqu)};\n",
            f"{syntaxUserOp.var_change_name(tmp_idx_var_name)}=({syntaxUserOp.var_change_name(tmp_idx_var_name)}+1)%({arrSyntaxType.get_size()});\n"]
        arrVar.postExpr = postCode
        genEqu.add_preEquations(preCode)

        return f"{syntaxUserOp.var_change_name(tmp_arr_var_name)}[{syntaxUserOp.var_change_name(tmp_idx_var_name)}]"
        #
        # # 这边都没有代码生成了，已经变成pre了
        # return self.equivalent_expr.generate_code(syntaxUserOp,genEqu)
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...

