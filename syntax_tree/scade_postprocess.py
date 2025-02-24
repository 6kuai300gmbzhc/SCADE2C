from syntax_tree.SyntaxClass import *
import syntax_tree.graph
# 记录函数之间依赖关系的单向图

def print_dependent_graph(graph):
    # 可以删
    out = ""
    for v in graph:
        out+=f"{v.getValue().name}\n"
        out += "TO:"
        for w in v.get_to_vertexes():
            out += f"({v.getValue().name} , {w.getValue().name})"
        out+="\n"
        out += "FROM:"
        for f in v.get_from_vertexes():
            out += f"({v.getValue().name} , {f.getValue().name})"
        out += "\n"
    print(out)
def post_process(root_scope: SyntaxPackageScope) -> None:
    """后处理流程，遍历语法树，进行一些修改方便代码生成"""
    print("============postProcess Begin============")
    userOp_dependent_graph = Graph()
    post_process_package(root_scope,userOp_dependent_graph)
    sorted_userOp=userOp_dependent_graph.topological_sort()
    if not sorted_userOp: raise UserOpDependentException("函数存在循环依赖")
    print("函数级拓扑排序完成，遍历顺序为:"+str(sorted_userOp))
    for userOp in sorted_userOp:
        post_process_userOp(userOp)
        # 按拓扑顺序去遍历各个函数，而非按package的顺序
        # 前面已经处理过open package，所以应该不会出现找不到引用的情况



def post_process_userOp(userOp:SyntaxUserOp) -> None:
    """在这里，遍历内部所有语句，对语句进行拓扑排序，并更新此函数的输入输出参数之间的依赖关系"""




def post_process_package(package: SyntaxPackageScope,userOp_dependent_graph:Graph) -> None:
    """package级别，即全局作用域和package作用域
    要处理open package"""
    open_packages(package)
    for name,userOp in package.userOpTable.items():
        build_userOp_dependent_graph(userOp, userOp_dependent_graph)


def build_userOp_dependent_graph(userOp:SyntaxUserOp, userOp_dependent_graph:Graph) -> None:
    """根据函数之间的依赖关系登记进入单向图"""
    for dependent_path in userOp.dependentFunctions:
        path_id=dependent_path.split("::")
        if len(path_id)>1:
            package_path=path_id[:-1]
            target_package=userOp.resolve_path(package_path)
        else:
            target_package=userOp.prevScope

        target_function=target_package.userOpTable[path_id[-1]]
        userOp_dependent_graph.addEdge(userOp,target_function)


def open_packages(package: SyntaxPackageScope) -> None:
    """处理open package情况"""
    open_list = package.openPackageList

    if not open_list: return
    for open_path in open_list:
        tar_package=package.resolve_path(open_path.split("::"))
        # 找到对应package后进行打开操作
        package.open(tar_package)
