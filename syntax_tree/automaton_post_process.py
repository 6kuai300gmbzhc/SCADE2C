from syntax_tree.SyntaxClass import *
import syntax_tree.scade_postprocess as scade_postprocess


# 遍历所有state，找到他修改的变量，与修改这些变量所用到的变量
# 要如何确定这些变量是上层的呢？就是需要查看是否在当前作用域找不到，而在上层作用域可以找到
# 将这些变量中，作为左值的变量记录起来，同时记录其对应的右值的变量才行
# equation，在遍历结束之后获取一个依赖单向图，应该通过这个单向图来找？
# 单向图直接存储了equation之间的依赖关系
# 最后的输出结果是rhsList这个东西
def post_process(automaton: SyntaxAutomaton):
    # 先遍历内部所有state
    for name, state in automaton.stateTable.items():
        post_process_state(state)


def post_process_state(state: SyntaxState):
    """对state进行后处理，处理state，和其内部的所有arrow，不需要给state进行排序
    所以得到对语句的graph后，整理出该state的整体的一个左值右值的情况
    """
    # 先拿左值，再看对应的右值
    # 找到左值对应的句子，找到这个句子的依赖句子，找到依赖句子的右值，依次看右值是不是上层句子
    state_graph = scade_postprocess.post_process_data_def(state)
    dependent_dict = dict()
    update_state_dependent_dict(state_graph, dependent_dict)
    for action in state.actionChildScopeList:
        action_graph = scade_postprocess.post_process_data_def(action)
        update_state_dependent_dict(action_graph, dependent_dict)


def update_state_dependent_dict(data_def:SyntaxDataDefScope) -> dict:
    """更新state中输入输出参数的依赖列表，更新存储于dict中"""
    # returnSymbolsTable的key就是左值，感谢之前的我整理出来这个东西
    # for name, return_symbol in data_def.returnSymbolsTable.items():
    #     # 找到这个返回的变量，所依赖的所有其他变量
    #     dependent_equations=return_symbol.equation.get_dependent_equations()
    #     for equation in dependent_equations:

