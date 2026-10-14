from typing import Optional
from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr, GenEqu, \
    generate_init_code
from syntax_tree.scade_postprocess import flatten_list
from syntax_tree.scade_type_inference import clock_inference_sync, type_inference_on_groups
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each, union_rhsLists
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_activate(SyntaxExpr):
    sub_operator: SyntaxExpr
    clock_expr:SyntaxClockExpr
    def post_process(self, data_def):
        self.returnNum=self.sub_operator.returnNum
        self.rhsList=self.sub_operator.rhsList
    def type_inference(self, lhs_type_list, data_def):
        self.set_clock_list([self.clock_expr])
        self.set_lhs_type(self.sub_operator.type_inference(lhs_type_list,data_def))
        self.appliedOpContextList=self.sub_operator.appliedOpContextList
        return self.lhsTypeList
    def generate_code(self, data_def, genEqu):
        tmp_names=list()
        for lhs_type in self.lhsTypeList:
            tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, lhs_type)
            tmp_names.append(tmp_name)
        self.sub_operator.set_applied_outC_name(self.appliedOpOutCName)
        depth=genEqu.depth
        sub_genEqu=GenEqu(depth+1)
        sub_code=assign_lhs_to_rhs_expr(tmp_names,self.sub_operator.generate_code(data_def,sub_genEqu),self.lhsTypeList,genEqu.depth+1,data_def)
        pre_code=f"{'    '*depth}if ({self.clock_expr.generate_code()}){{\n" \
                 f"{''.join(sub_genEqu.preEquations)}" \
                 f"{sub_code}" \
                 f"{'    '*depth}}}else{{\n" \
                 f"{''.join(generate_init_code(t,p,depth=depth+1) for t,p in zip(self.lhsTypeList,tmp_names))}"\
                 f"{'    '*depth}}}\n"
        genEqu.add_preEquations(pre_code)
        return tmp_names[0] if len(tmp_names)==1 else tmp_names
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.sub_operator=objects[0]
        self.clock_expr=objects[1]
    def set_param_expr(self,param_expr):
        self.sub_operator.set_param_expr(param_expr)
    def set_params(self,params:list['SyntaxExpr']):
        self.sub_operator.set_params(params)
    def get_applied_op(self):
        return self.sub_operator.get_applied_op()
