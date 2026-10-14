from typing import Optional
from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr, GenerateCode
from syntax_tree.scade_type_inference import clock_inference_sync
from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException, TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_restart(SyntaxExpr):
    # 需要重置的目标：
    # arrow 返回第一个周期
    # 带last值的变量设为last
    # 状态机设置为初始状态
    # time表达式重置
    # 调用的op需要reset
    # 我觉得搞不好不止这么多
    cond_expr:SyntaxExpr
    sub_operator:SyntaxExpr
    def post_process(self, data_def):
        # 默认处理函数都处理完成了
        self.returnNum=self.sub_operator.returnNum
        self.rhsList=self.sub_operator.rhsList
    def type_inference(self, lhs_type_list, data_def):
        self.cond_expr.type_inference([SyntaxType("bool")],data_def)
        result=self.sub_operator.type_inference(lhs_type_list,data_def)
        self.set_lhs_type(result)
        self.set_clock_list(self.sub_operator.lhsClockList)
        self.appliedOpContextList=self.sub_operator.appliedOpContextList
        return result
    def generate_code(self, data_def, genEqu):
        self.sub_operator.set_applied_outC_name(self.appliedOpOutCName)
        if self.get_applied_op() is None or not self.get_applied_op().hasInternalState:
            return self.sub_operator.generate_code(data_def,genEqu)

        cond_code=self.cond_expr.generate_code(data_def,genEqu)
        depth=genEqu.depth
        restart_func_name=f"{self.get_applied_op().get_global_name()}_reset"
        pre_code=f"{'    '*depth}if ({cond_code}){{\n" \
                 f"{GenerateCode.call_func_recursive(depth+1,self.appliedOpContextList,restart_func_name,f'outC->{self.appliedOpOutCName}')}" \
                 f"}}\n"
        genEqu.add_preEquations(pre_code)
        return self.sub_operator.generate_code(data_def,genEqu)
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.sub_operator=objects[0]
        self.cond_expr=objects[1]
    def set_params(self, params: list['SyntaxExpr']):
        """代码生产环节使用，设置用于产生代码的参数表达式"""
        self.paramExprs=params
        self.sub_operator.set_params(params)
    def set_param_expr(self,param_expr):
        """初始化时使用，设置用于类型推导等环节的参数表达式"""
        self.paramExpr=param_expr
        self.sub_operator.set_param_expr(param_expr)
    def get_applied_op(self):
        return self.sub_operator.get_applied_op()