import copy
import sys


from typing import TYPE_CHECKING

from syntax_tree.syntax_class.Exceptions import *
from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.pattern import SyntaxPattern
from syntax_tree.syntax_class.syntaxType import SyntaxType

if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.package import SyntaxPackageScope
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
    from syntax_tree.syntax_class.equation import SyntaxEquation
    from syntax_tree.syntax_class.scope.automaton import SyntaxAutomaton, SyntaxState
    from syntax_tree.syntax_class.scope.clocked_block import SyntaxIfBlock, SyntaxClockedScope, SyntaxMatchBlock
inferenced_op = list()


def type_inference(main_operator: 'SyntaxUserOp'):
    """对拓扑排序后，从后向前遍历userOP，进行类型推导
    有主节点的存在，最末端的userOp一定是主节点，且不是模板方法
    进行类型推导，与函数实例化操作
    从主节点开始向下遍历可以保证不会遇到模板类型的比较的情况
    """
    print("============type inference Begin============")
    type_inference_userOp(main_operator)
    inferenced_op.reverse()
    return inferenced_op
def remove_unnecessary_applied_expr(data_def:'SyntaxUserOp' or 'SyntaxState'):
    new_applied_exprs=list()
    for expr in data_def.apply_exprs:
        if expr.get_applied_op() is not None:
            new_applied_exprs.append(expr)
    data_def.apply_exprs=new_applied_exprs
inferenced_packages={}
def type_inference_userOp(userOp: 'SyntaxUserOp'):
    """
    类型推导，如果是模板函数要实例化，遍历的时候靠调用的path来找下一个目标函数
    """
    if userOp in inferenced_op:
        return
    inferenced_op.append(userOp)
    print(f"开始进行{userOp.get_global_name()}的类型推导")
    type_inference_dataDef(userOp)
    for out_param in userOp.outParams:
        if out_param.lastExpr is not None:
            out_param.lastExpr.type_inference([out_param.syntaxType],userOp)
    remove_unnecessary_applied_expr(userOp)
    package=userOp.get_my_package()
    if package not in inferenced_packages:
        for const_symbol in package.constSymbolTable.values():
            if const_symbol.used and const_symbol.valueExpr:
                const_symbol.valueExpr.type_inference([const_symbol.syntaxType],package)

    print(f"{userOp.get_global_name()}的类型推导结束")


def type_inference_dataDef(data_def: 'SyntaxDataDefScope'):
    for equation in data_def.equations:
        if equation.type != "control_block":
            try:
                type_inference_equation(equation, data_def)
            except Exception as e:
                print(f"发生错误的句子:{equation},在{data_def.get_global_name()}内", file=sys.stdout)
                raise e
        else:
            control_block = data_def.get_childScope(equation.controlBlockID)
            type_inference_control_block(control_block)


type_inference_control_block_handlers = {}

def type_inerence_control_block_handler(type_):
    def decorator(func):
        type_inference_control_block_handlers[type_] = func
        return func
    return decorator


def type_inference_control_block(control_block):
    type_ = control_block.type
    control_block_handler = type_inference_control_block_handlers[type_]
    return control_block_handler(control_block)

@type_inerence_control_block_handler("automaton")
def type_inference_automaton(control_block):
    # 感觉只是遍历每个state就行了，重点是每个句子，别的不管
    for state in control_block.stateTable.values():
        type_inference_dataDef(state)
        # 然后是状态转移部分
        for cond_expr, arrow in state.unlessTransitions:
            type_inference_arrow(cond_expr, arrow, state)
        for cond_expr, arrow in state.untilTransitions:
            type_inference_arrow(cond_expr, arrow, state)
        if state.synchroArrow is not None:
            type_inference_arrow(None, state.synchroArrow, state)
        remove_unnecessary_applied_expr(state)
@type_inerence_control_block_handler("if_block")
def type_inference_if_block(block:'SyntaxClockedScope'):
    def inference_sub_block(if_block:"SyntaxIfBlock"):
        if_block.conditionExpr.type_inference([SyntaxType("bool")],block)
        for sub_block in [if_block.thenBlock, if_block.elseBlock]:
            if isinstance(sub_block, str):
                # 是一个data_def
                data_def: SyntaxDataDefScope = block.get_childScope(sub_block)
                type_inference_dataDef(data_def)
            else:
                inference_sub_block(sub_block)
    return inference_sub_block(block.block)
@type_inerence_control_block_handler("match_block")
def type_inference_match_block(block:'SyntaxClockedScope'):
    match_block:SyntaxMatchBlock=block.block

    patterns=[case[0] for case in match_block.matchList]
    # 这里加一个检测pattern是否覆盖全部领域
    pattern_type=check_and_get_pattern_type(patterns,block)
    pattern_type=match_block.switchExpr.type_inference([pattern_type],block)[0].get_real_type()
    if pattern_type.type not in {"bool","enum"}:
        raise Exception(f"{block.name}作为clocked block只支持枚举类型和布尔类型")
    for case in match_block.matchList:
        pattern:SyntaxPattern=case[0]
        case_data_def:SyntaxDataDefScope=match_block.scope.get_childScope(case[1])
        type_inference_dataDef(case_data_def)

def check_and_get_pattern_type(patterns:list[SyntaxPattern],data_def:'SyntaxDataDefScope')->SyntaxType:
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
        pattern.type_inference([SyntaxType("any")],data_def)
        pattern.constValue=pattern.cal_const_value(pattern.lhsTypeList[0],data_def)
        cur_type=pattern.constValue.type
        if cur_type.get_real_type().type=="numeric":
            cur_type=SyntaxType("integer")# 锁死了
        elif cur_type.get_real_type().type=="enum" and not covered_all:
            if enum_names is None:
                enum_names=set([s.get_value() for s in cur_type.get_real_type().enumList])
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
def type_inference_arrow(cond_expr, arrow, data_def):
    if arrow is None: return
    if cond_expr is not None:
        cond_expr.type_inference([SyntaxType("bool")], data_def)
    if arrow.type == "if":
        for (sub_cond_expr, sub_arrow) in arrow.ifExprList:
            type_inference_arrow(sub_cond_expr, sub_arrow, data_def)
        type_inference_arrow(None, arrow.elseExpr, data_def)
    else:
        if arrow.action:
            action_scope = data_def.get_childScope(arrow.action)
            type_inference_dataDef(action_scope)


def type_inference_equation(equation: 'SyntaxEquation', data_def: 'SyntaxDataDefScope'):
    """
    根据句子的左值，来分配expr的返回类型值
    """
    for lhs in equation.lhs:
        if lhs.symbol_name == '_':
            equation.add_lhs_type(SyntaxType("any"))
        else:
            lhs_symbol = data_def.get_localVariable_InThisAndPreEnv(lhs.symbol_name)
            if not lhs_symbol:
                if equation.type == "emission" and data_def.have_signal_InThisAndPreEnv(lhs.symbol_name):
                    equation.add_lhs_type(SyntaxType("bool"))
                else:
                    raise UnknownIdentifierException(lhs)
            else:
                equation.add_lhs_type(lhs_symbol.syntaxType)
    # 现在获取了句子左值的所有类型变量，然后将他们分配给expr做推理
    equation.expr.type_inference(equation.lhsTypeList, data_def)
def type_inference_on_groups(sub_exprs: list['SyntaxExpr'], lhs_type_list_on_each, userOp):
    # 处理可以多返回的操作符
    for sub_expr in sub_exprs:
        sub_expr.type_inference(lhs_type_list_on_each,userOp)
    given_type_lists = [sub_expr.lhsTypeList for sub_expr in sub_exprs]
    # 他们返回的长度一定相等
    actual_types = list(map(min, zip(*given_type_lists)))
    actual_types = [copy.copy(t) for t in actual_types]
    # for i, given_types in enumerate(given_type_lists):
    #     for g, a in zip(given_types, actual_types):
    #         if g < a:
    #             sub_exprs[i].type_inference(actual_types, userOp)
    #             break
    return actual_types

def type_inference_on_binop(required_types:list['SyntaxType'],userOp:'SyntaxUserOp',sub_expr:'SyntaxExpr',need_type_confirm:bool):
    returned_types=sub_expr.type_inference(required_types,userOp)
    if not need_type_confirm:
        return returned_types
    min_type=min(returned_types)
    if not all([min_type==t for t in returned_types]):
        returned_types=sub_expr.type_inference([min_type]*len(required_types),userOp)
        min_type = min(returned_types)
    if not all([min_type==t for t in returned_types]):
        raise TypeMismatchException(f"{sub_expr}有类型{sub_expr.lhsTypeList}", required_types, userOp)
    return returned_types

def clock_inference_sync(clock_expr_list)->list:
    if all([sub_expr.fit(clock_expr_list[0]) for sub_expr in clock_expr_list]):
        for sub_expr in clock_expr_list:
            if not sub_expr.ignore_clock_check:
                return [sub_expr]
        return [SyntaxClockExpr.init_clock_any(clock_expr_list[0].scope)]
    else:
        raise IncompatibleClockException(clock_expr_list)
# def clock_inference_max_delay(clock_expr_list):
#     latest_expr=clock_expr_list[0]
#     for clock_expr in latest_expr:
def type_inference_const_symbol(rootPackage):
    for name, constSymbol in rootPackage.constSymbolTable.items():
        if constSymbol.valueExpr and (constSymbol.syntaxType.type=="any" or not constSymbol.valueExpr.lhsTypeList):
            constSymbol.valueExpr.type_inference([constSymbol.syntaxType],rootPackage)
            constSymbol.syntaxType=constSymbol.valueExpr.lhsTypeList[0]
    for _, packageScope in rootPackage.childScopeTable.items():
        type_inference_const_symbol(packageScope)
    if isinstance(rootPackage,SyntaxPackageScope):
        for _,user_op in rootPackage.userOpTable.items():
            type_inference_const_symbol(user_op)
def deepcopy_userOp(userOp):
    """天才"""
    tmp_prev_scope = userOp.prevScope
    userOp.prevScope = None
    copied_userOp = copy.deepcopy(userOp)
    userOp.prevScope = tmp_prev_scope
    copied_userOp.prevScope = tmp_prev_scope
    return copied_userOp
