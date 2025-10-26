
from syntax_tree.scade_type_inference import type_inference_on_groups
from syntax_tree.syntax_class.expression import SyntaxExpr

from typing import TYPE_CHECKING

from syntax_tree.syntax_class.expression.pattern import SyntaxPattern
from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:
    from syntax_tree.scade_generate import GenEqu, generate_tmp_symbol_and_register
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp

    from syntax_tree.syntax_class.scope.scope import SyntaxScope
class Switch_expr_CASE(SyntaxExpr):
    name:str
    '''id名称'''
    def post_process(self, userOp:'SyntaxUserOp'):
        pass
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # switch case情况需要提取判断表达式的类型，校验所有pattern的类型
        # case必须涵盖所有可能情况，如果非枚举类型，则一定需要有_pattern作为默认，枚举类型则不一定需要
        # 先进行上述的pattern类型推导
        patterns = [l[0] for l in self.objects[1]]
        pattern_type = check_and_get_pattern_type(patterns, data_def)
        pattern_type = self.objects[0].type_inference([pattern_type], data_def)[0]
        for pattern in patterns:
            if pattern.constValue:
                pattern.constValue.type = pattern_type
        # 然后是具体的表达式推导
        actual_types = type_inference_on_groups([l[1] for l in self.objects[1]], lhs_type_list, data_def)
        self.set_lhs_type(actual_types)
        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        tmp_var_symbol, tmp_var_name = generate_tmp_symbol_and_register(syntaxUserOp, self.lhsTypeList[0])
        pre_equations = f"switch({self.objects[0].generate_code(syntaxUserOp, genEqu)}){{\n"
        for elem in self.objects[1]:
            syntaxPattern = elem[0]
            syntaxExpr = elem[1]
            if syntaxPattern.value != '_':
                pre_equations += f"case {syntaxPattern.value}:\n {tmp_var_name} = {syntaxExpr.generate_code(syntaxUserOp, genEqu)};\nbreak;\n"
            else:
                pre_equations += f"default:\n {tmp_var_name} = {syntaxExpr.generate_code(syntaxUserOp, genEqu)};\nbreak;\n"
        pre_equations += "}\n"
        genEqu.preEquations.append(pre_equations)
        return tmp_var_name
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
def check_and_get_pattern_type(patterns:list[SyntaxPattern],data_def:SyntaxDataDefScope)->SyntaxType:
    """返回这些pattern是否可以涵盖全部情况，并且返回一个共同的类型
    如果不能涵盖全部情况则报错
    """
    pattern_type=SyntaxType("any")
    covered_all=False
    enum_names=None
    for pattern in patterns:
        if pattern.value=="_":
            covered_all=True
            continue
        pattern.constValue=pattern.constExpr.cal_const_value(SyntaxType("any"),data_def)
        cur_type=pattern.constValue.type
        if cur_type.get_real_type().type=="numeric":
            cur_type=SyntaxType("integer")# 锁死了
        elif cur_type.get_real_type().type=="enum" and not covered_all:
            if enum_names is None:
                enum_names=set([s.name for s in cur_type.get_real_type().enumList])
            enum_names.remove(pattern.constValue.value)
            # 如果是某个枚举类型就需要确认是否涵盖所有情况
        if cur_type<=pattern_type:
            pattern_type=cur_type
        else:
            raise Exception(f"{data_def.get_global_name()}中，存在switch语句中case的pattern不是一个类型")
    if enum_names is not None and len(enum_names)==0:
        covered_all=True
    if not covered_all:
        raise Exception(f"{data_def.get_global_name()}中，存在switch语句无法涵盖所有情况")
    return pattern_type