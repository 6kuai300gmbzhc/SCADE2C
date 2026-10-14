from typing import Optional
from syntax_tree.scade_postprocess import set_rhs_default
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr, expression_factory

from typing import TYPE_CHECKING
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register
from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Tempo_expr_TIMES(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        self.subExpr.post_process(userOp)
        set_rhs_default(self)
        self.subExpr.returnNum = sum([expr.returnNum for expr in self.objects[0]])
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 需要bool类型，子类型分别是signed和bool
        # 不支持列表
        if len(lhs_type_list) != 1 or lhs_type_list[0] != SyntaxType("bool"):
            raise TypeMismatchException(self, lhs_type_list, data_def)
        self.subExpr.type_inference([SyntaxType("signed"),SyntaxType("bool")],data_def)
        self.set_lhs_type(lhs_type_list)
        self.set_clock_list(self.subExpr.lhsClockList)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        counter_symbol, counter_name = generate_tmp_symbol_and_register(syntaxUserOp, SyntaxType("int32"), "counter",isOutPut=True)
        # preCode分为两部分，先根据init决定是否初始化，根据输入的布尔值决定是否自减
        # counter_name需要加入到outC之中
        depth = genEqu.depth
        int_expr_code,bool_expr_code=self.subExpr.generate_code(syntaxUserOp,genEqu)
        # 根据init初始化
        init_var = syntaxUserOp.set_init_var()
        pre_code = f"{'    ' * depth}kcg_int32 {counter_name};\n"
        pre_code += f"{'    ' * depth}if (outC->{init_var.name}){{\n" \
                    f"{'    ' * (depth + 1)}{counter_name} = {int_expr_code};\n" \
                    f"{'    ' * depth}}}\n" \
                    f"{'    ' * depth}else {{\n" \
                    f"{'    ' * (depth + 1)}{counter_name} = outC->{counter_name};\n" \
                    f"{'    ' * depth}}}\n"
        # 根据bool值进行自减，若已经小于0了就不变，然后如果bool为true则减一，如果为false则不变
        pre_code += f"{'    ' * depth}if ({counter_name}<kcg_lit_int32(0)) {{\n" \
                    f"{'    ' * (depth + 1)}outC->{counter_name} = {counter_name};\n" \
                    f"{'    ' * depth}}}\n" \
                    f"{'    ' * depth}else if ({bool_expr_code}){{\n" \
                    f"{'    ' * (depth + 1)}outC->{counter_name} = {counter_name} - kcg_lit_int32(1);\n" \
                    f"{'    ' * depth}}}\n" \
                    f"{'    ' * depth}else {{\n" \
                    f"{'    ' * (depth + 1)}outC->{counter_name} = {counter_name};\n" \
                    f"{'    ' * depth}}}\n"
        genEqu.add_preEquations(pre_code)
        # 返回的代码为当前countern是否为0

        out_code = f"({bool_expr_code}&&(outC->{counter_name} == kcg_lit_int32(0)))"
        return out_code
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: Optional[list] = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.subExpr = expression_factory("List_expr", "List_expr", scope, [self.objects[0]])
    def set_params(self,params:list['SyntaxExpr']):
        self.subExpr.objects[0]=params