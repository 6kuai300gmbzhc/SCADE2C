
from syntax_tree.scade_type_inference import type_inference_on_groups, check_and_get_pattern_type
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

from syntax_tree.syntax_class.expression.pattern import SyntaxPattern
from syntax_tree.syntax_class.hasRhs import union_rhsLists, add_rhs_to_each
from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
from syntax_tree.syntax_class.syntaxType import SyntaxType
from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr

if TYPE_CHECKING:

    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Switch_expr_CASE(SyntaxExpr):
    cond_expr:SyntaxExpr
    case_expr_list:list[[SyntaxPattern,SyntaxExpr]]
    def post_process(self, userOp:'SyntaxUserOp'):
        self.returnNum = self.case_expr_list[0][1].returnNum # 太逆天了,其实就是拿第一个case的expr
        self.rhsList = union_rhsLists([case[1].rhsList for case in self.case_expr_list])
        self.rhsList=add_rhs_to_each(self.cond_expr.rhsList,self.rhsList)
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # switch case情况需要提取判断表达式的类型，校验所有pattern的类型
        # case必须涵盖所有可能情况，如果非枚举类型，则一定需要有_pattern作为默认，枚举类型则不一定需要
        # 先进行上述的pattern类型推导
        patterns = [l[0] for l in self.case_expr_list]
        pattern_type = check_and_get_pattern_type(patterns, data_def)
        pattern_type = self.cond_expr.type_inference([pattern_type], data_def)[0]
        for pattern in patterns:
            if pattern.constValue:
                pattern.constValue.type = pattern_type
                pattern.type_inference([pattern_type],data_def)
        # 然后是具体的表达式推导
        actual_types = type_inference_on_groups([l[1] for l in self.case_expr_list], lhs_type_list, data_def)
        self.set_lhs_type(actual_types)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        tmp_names=list()
        for lhs_type in self.lhsTypeList:
            tmp_var_symbol, tmp_var_name = generate_tmp_symbol_and_register(syntaxUserOp, lhs_type)
            tmp_names.append(tmp_var_name)

        pre_equations = f"{'    '*(genEqu.depth)}switch({self.cond_expr.generate_code(syntaxUserOp, genEqu)}){{\n"
        for elem in self.case_expr_list:
            syntaxPattern = elem[0]
            syntaxExpr = elem[1]
            sub_gen=GenEqu(genEqu.depth+1)

            expr_code=syntaxExpr.generate_code(syntaxUserOp, sub_gen)
            pattern_code=syntaxPattern.generate_code(syntaxUserOp,genEqu)
            if pattern_code != '_':
                pre_equations += f"{'    '*(genEqu.depth)}case {pattern_code}:\n" \
                                 f"{''.join(sub_gen.preEquations)}" \
                                 f"{assign_lhs_to_rhs_expr(tmp_names,expr_code,self.lhsTypeList,genEqu.depth+1,syntaxUserOp)}" \
                                 f"{'    '*(genEqu.depth)}break;\n"
            else:
                pre_equations += f"{'    '*(genEqu.depth)}default:\n" \
                                 f"{''.join(sub_gen.preEquations)}" \
                                 f"{assign_lhs_to_rhs_expr(tmp_names,expr_code,self.lhsTypeList,genEqu.depth+1,syntaxUserOp)}" \
                                 f"{'    '*(genEqu.depth)}break;\n"
        pre_equations += f"{'    '*(genEqu.depth)}}}\n"
        genEqu.preEquations.append(pre_equations)
        return tmp_names[0] if len(tmp_names)==1 else tmp_names
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        self.cond_expr=objects[0]
        self.case_expr_list=objects[1]
