from syntax_tree.SyntaxClass import *
import syntax_tree.graph


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
        path_id = dependent_path.split("::")
        if len(path_id) > 1:
            package_path = path_id[:-1]
            target_package = userOp.resolve_path(package_path)
        else:
            target_package = userOp.prevScope

        target_function = target_package.userOpTable[path_id[-1]]
        userOp_dependent_graph.addEdge(target_function, userOp)


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
    for equation_vertex in equation_graph:
        for out_index in range(len(userOp.outParams)):
            out_param=userOp.outParams[out_index]
            if out_param.name not in equation_vertex.value.lhs: continue
            # 这就是找到了,然后开始深度优先搜索
            # 额，什么leetcode题目
            checked_set=set()
            dfs=deque([equation_vertex])
            while dfs:
                cur_vertex=dfs.pop()
                checked_set.add(cur_vertex)
                cur_equation=cur_vertex.value
                # 看看现在这个句子里面有没有输入参数，也就是看看带输出参数的句子依赖于有这个带输入参数的句子
                for in_index in range(len(userOp.inParams)):
                    in_param=userOp.inParams[in_index]
                    if in_param.name in cur_equation.rhs:
                        userOp.add_input_output_dependency(in_index,out_index)
                # 把新equation节点加入栈
                for nxt_vertex in cur_vertex.get_from_vertexes():
                    if nxt_vertex in checked_set: continue
                    dfs.append(nxt_vertex)
    print(userOp.get_global_name(),":",userOp.output2inputDependents)




def post_process_data_def(data_def: SyntaxDataDefScope) -> Graph:
    """对所有data_def类型，遍历其内部的所有语句，给出依赖关系，对语句进行拓扑排序,返回此作用域内的单向图"""
    graph = data_def.equationDependentGraph
    for src_equation in data_def.equations:
        # 右值依赖左值
        # 对这个句子，找到其他右值有其左值的句子，添加依赖关系
        for dst_equation in data_def.equations:
            if src_equation is not dst_equation and is_dependent(src_equation, dst_equation):
                # src依赖dst
                # 所以在dst到src有边
                graph.addEdge(dst_equation, src_equation)
    graph.topological_sort()
    # 在这里进行拓扑排序！在整理完其内部所有的依赖关系后进行排序
    return graph
