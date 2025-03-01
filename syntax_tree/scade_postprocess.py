from syntax_tree.SyntaxClass import *
import syntax_tree.graph
import itertools


# 记录函数之间依赖关系的单向图

def dependent_graph_str(graph):
    # 可以删
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


def post_process(root_scope: SyntaxPackageScope) -> None:
    """后处理流程，遍历语法树，进行一些修改方便代码生成"""
    print("============postProcess Begin============")
    userOp_dependent_graph = Graph()
    post_process_package(root_scope, userOp_dependent_graph)
    sorted_userOp = userOp_dependent_graph.topological_sort()
    if not sorted_userOp:
        raise UserOpDependentException(dependent_graph_str(userOp_dependent_graph))
    print("函数拓扑排序完成，遍历顺序为:" + str([op.get_global_name() for op in sorted_userOp]))
    for userOp in sorted_userOp:
        post_process_userOp(userOp)
        # 按拓扑顺序去遍历各个函数，而非按package的顺序
        # 前面已经处理过open package，所以应该不会出现找不到引用的情况


def post_process_package(package: SyntaxPackageScope, userOp_dependent_graph: Graph) -> None:
    """package级别，即全局作用域和package作用域
    要处理open package"""
    open_packages(package)
    for name, userOp in package.userOpTable.items():
        build_userOp_dependent_graph(userOp, userOp_dependent_graph)
    for sub_name, sub_package in package.childScopeTable.items():
        post_process_package(sub_package, userOp_dependent_graph)


def build_userOp_dependent_graph(userOp: SyntaxUserOp, userOp_dependent_graph: Graph) -> None:
    """根据函数之间的依赖关系登记进入单向图"""
    print(f"{userOp.get_global_name()}的依赖函数路径：{str(userOp.dependentFunctions)}")
    for dependent_path in userOp.dependentFunctions:

        target_userOp = userOp.find_userOp_by_path(dependent_path)
        if not target_userOp:
            raise UnknownIdentifierException(f"{userOp.get_global_name()}找不到{dependent_path}")
        userOp_dependent_graph.addEdge(target_userOp, userOp)


def open_packages(package: SyntaxPackageScope) -> None:
    """处理open package情况"""
    open_list = package.openPackageList

    if not open_list: return
    for open_path in open_list:
        tar_package = package.resolve_path(open_path.split("::"))
        # 找到对应package后进行打开操作
        package.open(tar_package)


def post_process_userOp(userOp: SyntaxUserOp) -> None:
    """在这里，遍历内部所有语句，对语句进行拓扑排序，并更新此函数的输入输出参数之间的依赖关系"""
    equation_graph = post_process_data_def(userOp)
    # 拿到完整的依赖关系图后，辨识输出参数和输入参数之间的关系
    # 这对吗这个
    # 在图中找到左值是out_param的句子，然后前向遍历，看看其他的句子里面有没有in_param
    # 如果这个uesrOp没有返回值的话，也要添加参数之间的依赖关系！！！！就是说这些返回值会有默认的依赖
    for equation_vertex in equation_graph:
        for out_index in range(len(userOp.outParams)):
            out_param = userOp.outParams[out_index]
            if out_param.name not in equation_vertex.value.lhs: continue
            # 这就是找到了,然后开始深度优先搜索
            # 额，什么leetcode题目
            checked_set = set()
            dfs = deque([equation_vertex])
            while dfs:
                cur_vertex = dfs.pop()
                checked_set.add(cur_vertex)
                cur_equation = cur_vertex.value
                # 看看现在这个句子里面有没有输入参数，也就是看看带输出参数的句子依赖于有这个带输入参数的句子
                for in_index in range(len(userOp.inParams)):
                    in_param = userOp.inParams[in_index]
                    if cur_equation.has_name_in_rhs(in_param.name):
                        userOp.add_input_output_dependency(in_index, out_index)
                # 把新equation节点加入栈
                for nxt_vertex in cur_vertex.get_from_vertexes():
                    if nxt_vertex in checked_set: continue
                    dfs.append(nxt_vertex)
    print(userOp.get_global_name(), "的输入输出参数之间因果关系为:", userOp.output2inputDependents)


def post_process_data_def(data_def: SyntaxDataDefScope) -> Graph:
    """对所有data_def类型，遍历其内部的所有语句，给出依赖关系，对语句进行拓扑排序,返回此作用域内的单向图"""
    # 先看一眼其内部所有的语句,把依赖关系建立起来
    for equation in data_def.equations:
        post_process_equation(equation, data_def)
    graph = data_def.equationDependentGraph
    for src_equation in data_def.equations:
        # 右值依赖左值
        # 对这个句子，找到其他右值有其左值的句子，添加依赖关系
        for dst_equation in data_def.equations:
            if src_equation is not dst_equation and src_equation.dependent_on_equation(dst_equation):
                # src依赖dst
                # 所以在dst到src有边
                graph.addEdge(dst_equation, src_equation)
    graph.topological_sort()
    # 在这里进行拓扑排序！在整理完其内部所有的依赖关系后进行排序
    return graph


def post_process_equation(equation: SyntaxEquation, data_def) -> None:
    """这里要处理所有语句的变量依赖关系，从预处理阶段挪到这里了"""
    # 只有control_block有不同的地方，其他都一样
    if equation.type != "control_block":
        post_process_expr(equation.expr, data_def)
        equation.set_rhs()
    else:
        # todo 状态机后处理流程
        pass


post_process_expr_handlers = {}


def post_expr_handler(type_):
    def decorator(func):
        post_process_expr_handlers[type_] = func
        return func

    return decorator


def post_process_expr(expr, data_def):
    """expr后处理，进行变量校验，判断因果关系"""
    type_ = expr.type
    flat_list = flatten_list(expr.objects)

    for sub_expr in flat_list:
        if type(sub_expr) == SyntaxExpr:
            post_process_expr(sub_expr, data_def)
    if type_ in post_process_expr_handlers.keys():
        generate_expr_handler = post_process_expr_handlers[type_]
        generate_expr_handler(expr, data_def)
    else:
        # 默认的情况下，expr的rhs是各子expr之和，合并成一个
        # 我一定会处理函数调用的情况，所以这里就没有operator了！
        tar_rhs = set()
        for sub_expr in flat_list:
            if type(sub_expr) != SyntaxExpr: continue
            for rhs in sub_expr.rhsList:
                tar_rhs |= rhs
        expr.set_rhs(tar_rhs)


@post_expr_handler('Id_expr')
def post_Id_expr(expr: SyntaxExpr, data_def):
    if expr.subType == "ID": return
    name = expr.objects[0]
    if expr.subType == "Path_id":
        if "::" in name: return  # 是path说明是常量
    else:
        name = name[1:]  # 去掉开头的'
    # id_expr仅有单个返回值，设置rhs
    expr.set_rhs([name])


@post_expr_handler('List_expr')
def post_List_expr(expr: SyntaxExpr, data_def):
    # 列表有多个返回值
    # 嵌套列表视为其完全展开格式
    # 这里对这种情况进行处理,如果可以保证按后序处理语法树结构，就不用递归的检查了
    if not expr.objects: return
    expr_list = expr.objects[0]
    new_object_list = list()
    for sub_expr in expr_list:
        expr.add_rhs(sub_expr)
        if sub_expr.type == "List_expr":
            # 因为还需要考虑到函数调用的因素，所以这里不可能全部的将list展开
            for o in sub_expr.objects[0]:
                new_object_list.append(o)
        else:
            new_object_list.append(sub_expr)
    expr.objects[0] = new_object_list


@post_expr_handler('Apply_expr')
def post_Apply_expr(expr, data_def):
    """遇到函数调用，根据输入，输出参数来确定对应的依赖关系"""
    # 处理一下operator的情况，情况比较复杂，需要分配到每个函数自行解决问题
    operator = expr.objects[0]
    type_=operator.subtype
    if type_ in post_process_operator_handlers.keys():
        generate_operator_handler = post_process_operator_handlers[type_]
        generate_operator_handler(operator,expr, data_def)


post_process_operator_handlers = {}


def post_operator_handler(type_):
    def decorator(func):
        post_process_operator_handlers[type_] = func
        return func

    return decorator


@post_operator_handler('Path_id')
def post_operator_Path_id(operator:SyntaxOperator,expr,data_def):
    """最常用的，函数调用部分，找到目标函数，然后查看输入输出依赖关系，更新expr的右值"""
    # 找到目标函数
    tar_userOp = data_def.find_userOp_by_path(operator.objects[0])
    if not tar_userOp:
        raise UnknownIdentifierException(f"{data_def.get_global_name()}找不到{operator.objects[0]}")
    # 找到了之后，根据这个函数的依赖关系确定这个表达式的依赖关系



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
