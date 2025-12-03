from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr
from syntax_tree.scade_postprocess import flatten_list
from syntax_tree.scade_type_inference import clock_inference_sync, type_inference_on_groups
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each, union_rhsLists
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_activateDefault(SyntaxExpr):
    sub_operator:SyntaxExpr
    cond_expr:SyntaxExpr
    default_expr:SyntaxExpr
    paramExpr:SyntaxExpr
    def post_process(self, data_def):
        op_rhs_list = union_rhsLists([self.sub_operator.rhsList, self.default_expr.rhsList])
        op_rhs_list = add_rhs_to_each(self.cond_expr.rhsList, op_rhs_list)
        self.rhsList=op_rhs_list
        self.returnNum=self.sub_operator.returnNum
    def type_inference(self, lhs_type_list, data_def):
        # 三个组件，一个op，一个bool表达式，一个默认表达式
        self.cond_expr.type_inference([SyntaxType("bool")], data_def)

        actual_types=type_inference_on_groups([self.default_expr,self.sub_operator],lhs_type_list,data_def)
        self.set_lhs_type(actual_types)
        apply_userOp = self.get_applied_op()
        if apply_userOp is not None:
            self.add_applied_Op(apply_userOp, self.sub_operator.appliedOpContextList)

        # 这四个必须是同一时钟
        self.set_clock_list(clock_inference_sync(
            flatten_list([expr.lhsClockList for expr in [self.cond_expr,self.default_expr,self.sub_operator,self.paramExpr]])))
        return self.lhsTypeList
    def generate_code(self, data_def, genEqu):
        depth = genEqu.depth
        cond_code = self.cond_expr.generate_code(data_def, genEqu)
        tmp_names=list()
        for lhs_type in self.lhsTypeList:
            tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, lhs_type)
            tmp_names.append(tmp_name)

        default_code = assign_lhs_to_rhs_expr(tmp_names, self.default_expr.generate_code(data_def, genEqu)
                                              , self.lhsTypeList, depth, data_def)
        self.sub_operator.set_applied_outC_name(self.appliedOpOutCName)
        activate_code = assign_lhs_to_rhs_expr(tmp_names,
                                               self.sub_operator.generate_code(data_def, genEqu),
                                               self.lhsTypeList, depth, data_def)
        pre_code = f"{'    ' * depth}if({cond_code}){{\n" \
                   f"{activate_code}" \
                   f"{'    ' * depth}}}\n" \
                   f"{'    ' * depth}else {{\n" \
                   f"{default_code}" \
                   f"{'    ' * depth}}}\n"
        genEqu.add_preEquations(pre_code)
        return tmp_names[0] if len(tmp_names)==1 else tmp_names
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.sub_operator = self.objects[0]
        self.cond_expr = self.objects[1]
        self.default_expr = self.objects[2]
    def set_param_expr(self,param_expr):
        self.paramExpr=param_expr
        self.sub_operator.set_param_expr(param_expr)
    def set_params(self,params:list['SyntaxExpr']):
        self.paramExprs=params
        self.sub_operator.set_params(params)
    def get_applied_op(self):
        return self.appliedOp