from syntax_tree.SyntaxClass import *
import syntax_tree.scade_postprocess as scade_postprocess


def merge_dict(*dicts: dict[str, set[str]]) -> dict[str, set[str]]:
    # 按key融合对set取并集
    result = {}
    for d in dicts:
        for key, value in d.items():
            if key in result:
                result[key] = result[key].union(value)
            else:
                result[key] = value
    return result


# todo 状态机转移部分的语句需要加入右值列表中
def post_process_automaton(automaton: SyntaxAutomaton):
    # 遍历所有state，找到他修改的变量，与修改这些变量所用到的变量
    # 要如何确定这些变量是上层的呢？就是需要查看是否在当前作用域找不到，而在上层作用域可以找到
    # 将这些变量中，作为左值的变量记录起来，同时记录其对应的右值的变量才行
    # equation，在遍历结束之后获取一个依赖单向图，应该通过这个单向图来找？
    # 单向图直接存储了equation之间的依赖关系
    # 最后的输出结果是rhs_dict这个东西
    rhs_dict = dict()
    for name, state in automaton.stateTable.items():
        rhs_dict=merge_dict(rhs_dict,post_process_state(state))
    return rhs_dict


def post_process_if_block(clock_scope: SyntaxClockedScope):
    # 返回一个字典{左值变量名字->[依赖的右值变量名字]}
    return post_process_cond_block(clock_scope.block)


def post_process_cond_block(block: SyntaxIfBlock) -> dict:
    """处理if_block"""
    scade_postprocess.post_process_expr(block.conditionExpr, block.scope)
    rhs_dict = dict()
    for sub_block in [block.thenBlock, block.elseBlock]:
        if isinstance(sub_block, str):
            # 是一个data_def
            data_def: SyntaxDataDefScope = block.scope.get_childScope(sub_block)
            scade_postprocess.post_process_data_def(data_def)
            rhs_dict=merge_dict(rhs_dict,update_dependent_dict(data_def))
        else:
            rhs_dict=merge_dict(rhs_dict,post_process_cond_block(sub_block))
    rhs_dict = dict(zip(
        rhs_dict.keys(), scade_postprocess.add_rhs_to_each(block.conditionExpr.rhsList, list(rhs_dict.values()))))
    return rhs_dict


def post_process_state(state: SyntaxState)->dict[str,set[str]]:
    """对state进行后处理，处理state，和其内部的所有arrow，不需要给state进行排序
    所以得到对语句的graph后，整理出该state的整体的一个左值右值的情况
    """
    # 先拿左值，再看对应的右值
    # 找到左值对应的句子，找到这个句子的依赖句子，找到依赖句子的右值，依次看右值是不是上层句子
    scade_postprocess.post_process_data_def(state)
    # key 输出名字，value输入名字
    dependent_dict= update_dependent_dict(state)

    arrow_rhs_set = set()
    for cond_expr, arrow in state.unlessTransitions:
        arrow_rhs_set.update(post_process_arrow(cond_expr, arrow, state))
    for cond_expr, arrow in state.untilTransitions:
        arrow_rhs_set.update(post_process_arrow(cond_expr, arrow, state))
    if state.synchroArrow is not None:
        arrow_rhs_set.update(post_process_arrow(None, state.synchroArrow, state))

    for action in state.actionChildScopeList:
        scade_postprocess.post_process_data_def(action)
        dependent_dict=merge_dict(dependent_dict,update_dependent_dict(action))
    add_rhs_to_each_dependent_variable(arrow_rhs_set, dependent_dict)
    return dependent_dict


def add_rhs_to_each_dependent_variable(tar_set: set[str], dependent_dict: dict[str, set[str]]):
    for dependent_rhs in dependent_dict.values():
        dependent_rhs |= tar_set


def post_process_arrow(cond_expr, arrow, data_def) -> set[str]:
    if arrow is None: return set()
    arrow_rhs_set = set()
    if cond_expr is not None:
        scade_postprocess.post_process_expr(cond_expr, data_def)
        arrow_rhs_set = arrow_rhs_set.union(*cond_expr.rhsList)
    if arrow.type == "if":
        for (sub_cond_expr, sub_arrow) in arrow.ifExprList:
            arrow_rhs_set.update(post_process_arrow(sub_cond_expr, sub_arrow, data_def))
        arrow_rhs_set.update(post_process_arrow(None, arrow.elseExpr, data_def))
    return arrow_rhs_set


def update_dependent_dict(data_def: SyntaxDataDefScope) -> dict[str,set[str]]:
    """更新state中输入输出参数的依赖列表，更新存储于dict中"""
    # returnSymbolsTable的key就是左值，感谢之前的我整理出来这个东西
    out_dict = dict()
    for symbol_name in data_def.returnSymbolsTable:
        out_dict[symbol_name] = set()
        dependent_params = scade_postprocess.find_non_intermediate_dependencies(data_def, symbol_name)
        for dependent_param_name in dependent_params:
            if data_def.is_param_declared_externally(dependent_param_name):
                out_dict[symbol_name].add(dependent_param_name)
    return out_dict
