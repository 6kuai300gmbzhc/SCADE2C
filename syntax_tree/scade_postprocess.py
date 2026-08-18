from collections import deque
from syntax_tree.graph import Graph
import syntax_tree.control_block_post_process as control_block_post_process
from syntax_tree.syntax_class.Exceptions import *
from typing import TYPE_CHECKING

from syntax_tree.syntax_class.expression import SyntaxExpr
from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.pattern import SyntaxPattern
from syntax_tree.syntax_class.hasRhs import HasRhs

if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.package import SyntaxPackageScope
    from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
    from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
    from syntax_tree.syntax_class.equation import SyntaxEquation, LeftItemId
    from syntax_tree.syntax_class.scope.automaton import SyntaxAutomaton
    from syntax_tree.syntax_class.scope.clocked_block import SyntaxIfBlock, SyntaxMatchBlock, SyntaxClockedScope
"""
后处理流程，在预处理过程完成对语法树的构建后，进行这个流程来进行排序，与其他相关的处理
代码生成过程应该只生成代码，而不对语法树结构有任何过多的修改，所以后处理流程负责将语法树的结构修正为可以直接逐句生成代码的方式
根据main_operator路径找到主节点，根据preprocess过程中记录的函数调用情况，来递归的建立函数间的依赖单向图
先遍历语法树中所有package，进行打开的操作，删除所有不在单向图中的userOp
对这个单向图进行拓扑排序，按照拓扑排序后的顺序再次遍历userOp
遍历userOp中的每个句子
遍历句子中的每个expr，记录这个expr所需要的右值，考虑到多返回值的情况，expr的右值是set的列表，从左到右记录每个返回值的右值集合
同时，记录expr所返回的左值类型，同样是一个列表，长度要和右值列表所对应
遍历完expr后，让句子的左值链接句子的右值，记录这个句子左右值之间的依赖关系
对userOp中的句子进行排序
排序后，建立userOp中输入输出变量之间的因果关系，因为按照拓扑排序进行遍历所以可以保证其内部所调用的函数都经过了遍历，已经建立完成了输入输出变量的因果关系

对状态机的情况，需要先按照data_def的方式遍历句子，排序，然后建立每个state中对外界变量的修改。
状态机将每个state中建立起来的因果关系取并集，作为整体状态机的因果关系
"""
"""
以及还需要处理模板函数实例化的问题，这个时候就要用到输入的主节点参数路径了。
根据输入主节点路径找到对应函数
递归的遍历其调用的函数
    如果 函数是模板函数：
        根据调用的参数类型决定实例化的类型
        如果该类型已经被实例化：
            不管
        否则：
            实例化该函数
        将调用的expr的path_id修正为实例化后的名字
    将这个函数调用的其他函数入栈

函数实例化流程：
    生成一个新的名字
    先遍历变量声明，修改为对应类型
    然后遍历语句，找到
        1：类型转换语句
        2：函数调用语句
    修改语句中的类型
"""


# 记录函数之间依赖关系的单向图,有时候要把它打印出来用来调试

def dependent_graph_str(graph):
    out = ""
    for v in graph:
        out += f"{v.getValue().name}\n"
        out += "TO:"
        for w in v.get_to_vertexes():
            out += f"({v.getValue().name} , {w.getValue().name})"
        out += "\n"
        out += "FROM:"
        for f in v.get_from_vertexes():
            out += f"({v.getValue().name} , {f.getValue().name})"
        out += "\n"
    return out


def post_process(root_scope: 'SyntaxPackageScope', main_operator_path: str):
    """后处理流程，遍历语法树，进行一些修改方便代码生成"""
    print("============postProcess Begin============")

    userOp_dependent_graph = Graph()
    # 现在要找到主节点
    path = main_operator_path.split("::")
    main_operator = root_scope.resolve_path(path[:-1]).get_userOp(path[-1])
    if not main_operator:
        raise UnknownIdentifierException("找不到主节点：" + main_operator_path)
    # 处理openpackage
    open_packages(root_scope)
    # 从主节点开始建图
    build_userOp_dependent_graph(main_operator, userOp_dependent_graph)
    sorted_order = userOp_dependent_graph.topological_sort()
    if not sorted_order:
        raise UserOpDependentException(dependent_graph_str(userOp_dependent_graph))
    print("函数拓扑排序完成，遍历顺序为:" + str([op.get_global_name() for op in sorted_order]))

    post_process_package(root_scope, userOp_dependent_graph)
    # 把没用到的userOp都删了

    for userOp in sorted_order:
        post_process_userOp(userOp)
        # 按拓扑顺序去遍历各个函数，而非按package的顺序
        # 前面已经处理过open package，所以应该不会出现找不到引用的情况
    print("============postProcess END============")
    return sorted_order, main_operator

def open_packages(root_package: 'SyntaxPackageScope'):
    root_package.open_packages()
    for sub_package in root_package.childScopeTable.values():
        open_packages(sub_package)
def post_process_package(package: 'SyntaxPackageScope', userOpGraph: Graph) -> None:
    """package级别，即全局作用域和package作用域
    要处理open package"""
    for sub_name, sub_package in package.childScopeTable.items():
        post_process_package(sub_package, userOpGraph)
    # 去残留，只要用到OP
    userOpTable = dict()
    for op_name, userOp in package.userOpTable.items():
        if userOpGraph.getVertex(userOp) is not None:
            userOpTable[op_name] = userOp
    package.userOpTable = userOpTable
    for const_symbol in package.constSymbolTable.values():
        if const_symbol.valueExpr is not None:
            const_symbol.valueExpr.post_process(package)


def build_userOp_dependent_graph(userOp: 'SyntaxUserOp', userOp_dependent_graph: Graph) -> None:
    """根据函数之间的依赖关系登记进入单向图"""
    print(f"{userOp.get_global_name()}的依赖函数路径：{str(userOp.dependentFunctions)}")
    userOp_dependent_graph.addVertex(userOp)  # 先把自己加进去
    for dependent_path in userOp.dependentFunctions:
        target_userOp = userOp.check_and_get_userOp(dependent_path)
        if not target_userOp:
            raise UnknownIdentifierException(f"{userOp.get_global_name()}找不到{dependent_path}")
        userOp_dependent_graph.addEdge(target_userOp, userOp)
        build_userOp_dependent_graph(target_userOp, userOp_dependent_graph)

def post_process_userOp(userOp: 'SyntaxUserOp') -> None:
    """在这里，遍历内部所有语句，对语句进行拓扑排序，并更新此函数的输入输出参数之间的依赖关系"""
    # 如果函数是imported的话，就假设输入输出之间全都有关系
    if userOp.isImported:
        userOp.output2inputDependents = [[i for i in range(len(userOp.inParams))] * len(userOp.outParams)]
    else:
        equation_graph = post_process_data_def(userOp)
        build_userOp_output2inputDependents(userOp, equation_graph)
    for out_param in userOp.outParams:
        if out_param.lastExpr is not None:
            out_param.lastExpr.post_process(userOp)
    print(userOp.get_global_name(), "的输入输出参数之间因果关系为:", userOp.output2inputDependents)


def build_userOp_output2inputDependents(userOp: 'SyntaxUserOp', equation_graph):
    """拿到完整的依赖关系图后，辨识输出参数和输入参数之间的关系
    这对吗这个
    在图中找到左值是out_param的句子，然后前向遍历，看看其他的句子里面有没有in_param
    如果这个uesrOp没有返回值的话，也要添加参数之间的依赖关系！！！！就是说这些返回值会有默认的依赖
    """
    if not userOp.inParams:
        userOp.output2inputDependents =[[] for _ in range(len(userOp.outParams))]
        # 没有输入参数，则依赖表就是空，输出完全不依赖输入
        return  # 没有输入参数，非常好，直接返回
    # 如果这个函数没有输出呢？
    if not userOp.outParams:
        for in_index in range(len(userOp.inParams)):
            in_name = userOp.inParams[in_index].name
            for equation in userOp.equations:
                if equation.has_name_in_rhs(in_name):
                    userOp.add_input_output_dependency(in_index, 0)  # 放一个虚空索引
                    break
        return
    for out_index in range(len(userOp.outParams)):
        out_param = userOp.outParams[out_index]
        # 要先找到out_param所对应的equation，然后再根据其推出变量依赖的其他语句，直到找到in_param
        dependent_params = find_non_intermediate_dependencies(userOp, out_param.name)
        for in_index in range(len(userOp.inParams)):
            in_param = userOp.inParams[in_index]
            if in_param.name in dependent_params:
                userOp.add_input_output_dependency(in_index, out_index)


def find_non_intermediate_dependencies(data_def: 'SyntaxDataDefScope', param_name: str) -> list:
    """在指定作用域里，找到指定变量名所依赖的全部非局部变量的名字"""

    out_equation_list = data_def.get_equation_by_lhs(param_name)
    if out_equation_list is None:
        raise Exception(f"{data_def.get_global_name()}没有以{param_name}为左值的句子，这不对")
    equation_stack = deque([out_equation_list])
    var_stack = deque([param_name])
    out_list = list()
    while equation_stack:
        cur_equation_list = equation_stack.pop()
        cur_var_name = var_stack.pop()
        cur_rhs_list = {item for e in cur_equation_list for item in e.get_rhs_list_by_name(cur_var_name)}
        if not cur_rhs_list: continue
        for rhs_name in cur_rhs_list:
            # 是局部变量，就一定有以自己为右值的语句
            nxt_equation_list = data_def.get_equation_by_lhs(rhs_name)
            if nxt_equation_list is None:
                out_list.append(rhs_name)
            else:
                equation_stack.extend([nxt_equation_list])
                var_stack.append(rhs_name)
    return out_list


def post_process_data_def(data_def: 'SyntaxDataDefScope') -> Graph:
    """对所有data_def类型，遍历其内部的所有语句，给出依赖关系，对语句进行拓扑排序,返回此作用域内的单向图
    除此之外还需要给出变量之间的依赖关系单向图
    """
    # 先看一眼其内部所有的语句,把依赖关系建立起来
    if not data_def.equations: return data_def.equationDependentGraph
    for equation in data_def.equations:
        post_process_equation(equation, data_def)
    graph = data_def.equationDependentGraph
    # 这里是双重循环，是因为此处是建立单向图的过程
    for src_equation in data_def.equations:
        src_equation.set_vertex(graph.addVertex(src_equation))
        # 右值依赖左值
        # 对这个句子，找到其他右值有其左值的句子，添加依赖关系
        for dst_equation in data_def.equations:
            if src_equation is dst_equation: continue
            correspond_lhs = src_equation.dependent_on_equation_directly_and_get_correspond_lhs(dst_equation)
            # src依赖dst
            # 所以在dst到src有边
            # 把对应的左值赋给边
            if correspond_lhs is not None:
                graph.addEdge(dst_equation, src_equation, arrow=correspond_lhs)
    data_def.equations = graph.topological_sort()
    # 在这里进行拓扑排序！在整理完其内部所有的依赖关系后进行排序
    if not data_def.equations:
        raise UserOpDependentException(data_def.get_global_name())
    make_symbol_output_again(data_def.equations,data_def)
    return graph

def make_symbol_output_again(equations:list["SyntaxEquation"],data_def):
    '''想出来这个名字，我真应该少上点网了
    因为时态算子等原因，右值变量并不一定与左值变量存在因果关系
    所以在进行拓扑排序后，可能会有变量先使用再赋值的关系
    所以这个环节把这种变量设置为output，这样就没问题了（确信）
    '''
    for i in range(len(equations)):
        src_equation=equations[i]
        used_symbol_names=src_equation.allUsedSymbolNames
        for j in range(i+1,len(equations)):
            dst_equation=equations[j]
            lhs=[l.symbol_name for l in dst_equation.lhs]
            for l in lhs:
                if l in used_symbol_names:
                    symbol=data_def.get_localVariable_InThisAndPreEnv(l)
                    symbol.isOutput=True

def post_process_equation(equation: 'SyntaxEquation', data_def) -> None:
    """这里要处理所有语句的变量依赖关系，从预处理阶段挪到这里了"""
    # 只有control_block有不同的地方，其他都一样
    if equation.type != "control_block":
        equation.expr.post_process(data_def)
        equation.rhsList = equation.expr.rhsList
        # 将equation的返回值与expr的返回值相对应
    else:
        # controlblock要
        control_block = data_def.get_childScope(equation.controlBlockID)
        rhs_dict = post_process_control_block(control_block)
        for lhs in equation.lhs:
            equation.add_rhs(rhs_dict[lhs.symbol_name])
    if len(equation.lhs) == 0 and len(equation.rhsList) != 0:
        # 填一下左值方便排序
        from syntax_tree.syntax_class.equation import LeftItemId
        equation.lhs = [LeftItemId(equation.scope, "_")] * len(equation.rhsList)
    if len(equation.lhs) != len(equation.rhsList):
        print("!!!不对")
        print(equation)
        print(equation.type)
        print(equation.lhs)
        print(equation.rhsList)
        print(equation.lhs2RhsDict)
        raise Exception(f"equation{equation}的左右值长度不一样")
    for i in range(len(equation.lhs)):
        symbol_name = equation.lhs[i].symbol_name
        if equation.lhs2RhsDict.get(symbol_name) is None:
            equation.lhs2RhsDict[symbol_name] = set()
        equation.lhs2RhsDict[symbol_name].update(equation.rhsList[i])
        if symbol_name in equation.rhsList[i]:
            raise UserOpDependentException(data_def.get_global_name() + f"有句子{equation}依赖自身了")
    if equation.expr:
        equation.allUsedSymbolNames=equation.expr.allUsedSymbolNames


def set_rhs_default(expr):
    # 默认的情况下，expr的rhs是各子expr之和，合并成一个
    # 我一定会处理函数调用的情况，所以这里就没有operator了
    flat_list = flatten_list(expr.objects)
    tar_rhs = set()
    for sub_expr in flat_list:
        if not isinstance(sub_expr, SyntaxExpr): continue
        for rhs in sub_expr.rhsList:
            tar_rhs |= rhs
    expr.set_rhs(tar_rhs)


def process_subexpr_default(expr, data_def):
    """默认的子expr后处理，就是挨个遍历一下，有clockExpr"""
    """默认的子expr后处理，就是挨个遍历一下，有clockExpr"""
    flat_list = flatten_list(expr.objects)
    for sub_expr in flat_list:
        if isinstance(sub_expr, SyntaxExpr) or isinstance(sub_expr, SyntaxClockExpr) or isinstance(sub_expr,
                                                                                                   SyntaxPattern):
            sub_expr.post_process(data_def)

def after_post_process(expr:SyntaxExpr,data_def):
    '''后处理的后处理，这里统计expr所有用到的变量之类的'''
    flat_list = flatten_list(expr.objects)
    for sub_expr in flat_list:
        if issubclass(type(sub_expr),HasRhs):
            expr.allUsedSymbolNames.update(sub_expr.allUsedSymbolNames)
def flatten_list(input_list: list) -> list:
    """把嵌套列表展开，不是列表的输入也返回一个列表"""
    if not type(input_list) == list:
        return [input_list]
    output = []
    for item in input_list:
        if type(item) == list:
            flattened = flatten_list(item)
            for sub_item in flattened:
                output.append(sub_item)
        else:
            output.append(item)
    return output


post_process_control_block_handlers = {}


def post_control_block_handler(type_):
    def decorator(func):
        post_process_control_block_handlers[type_] = func
        return func

    return decorator


def post_process_control_block(control_block):
    type_ = control_block.type
    control_block_handler = post_process_control_block_handlers[type_]
    return control_block_handler(control_block)


@post_control_block_handler('automaton')
def post_automaton(automaton: 'SyntaxAutomaton'):
    # 返回一个字典{左值变量名字->[依赖的右值变量名字]}
    return control_block_post_process.post_process_automaton(automaton)


@post_control_block_handler('if_block')
def post_if_block(if_block: 'SyntaxClockedScope'):
    # 返回一个字典{左值变量名字->[依赖的右值变量名字]}
    return control_block_post_process.post_process_if_block(if_block)


@post_control_block_handler('match_block')
def post_match_block(match_block: 'SyntaxClockedScope'):
    # 返回一个字典{左值变量名字->[依赖的右值变量名字]}
    return control_block_post_process.post_process_match_block(match_block)
