import copy
import sys

from syntax_tree.SyntaxClass import *
import functools

from syntax_tree.scade_const_expression import cal_const_expr

inferenced_op = list()


def type_inference(main_operator: SyntaxUserOp):
    """对拓扑排序后，从后向前遍历userOP，进行类型推导
    有主节点的存在，最末端的userOp一定是主节点，且不是模板方法
    进行类型推导，与函数实例化操作
    从主节点开始向下遍历可以保证不会遇到模板类型的比较的情况
    """
    print("============type inference Begin============")
    type_inference_userOp(main_operator)
    inferenced_op.reverse()
    return inferenced_op


def type_inference_userOp(userOp: SyntaxUserOp):
    """
    类型推导，如果是模板函数要实例化，遍历的时候靠调用的path来找下一个目标函数
    """
    if userOp in inferenced_op:
        return
    inferenced_op.append(userOp)
    print(f"开始进行{userOp.get_global_name()}的类型推导")
    type_inference_dataDef(userOp)
    print(f"{userOp.get_global_name()}的类型推导结束")


def type_inference_dataDef(data_def: SyntaxDataDefScope):
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


def type_inference_control_block(control_block):
    # 目前就automaton
    # 感觉只是遍历每个state就行了，重点是每个句子，别的不管
    if control_block.type == "automaton":
        for state in control_block.stateTable.values():
            type_inference_dataDef(state)
            # 然后是状态转移部分
            for cond_expr, arrow in state.unlessTransitions:
                type_inference_arrow(cond_expr, arrow, state)
            for cond_expr, arrow in state.untilTransitions:
                type_inference_arrow(cond_expr, arrow, state)
            if state.synchroArrow is not None:
                type_inference_arrow(None, state.synchroArrow, state)


def type_inference_arrow(cond_expr, arrow, data_def):
    if arrow is None: return
    if cond_expr is not None:
        type_inference_expr(cond_expr, [SyntaxType("bool")], data_def)
    if arrow.type == "if":
        for (sub_cond_expr, sub_arrow) in arrow.ifExprList:
            type_inference_arrow(sub_cond_expr, sub_arrow, data_def)
        type_inference_arrow(None, arrow.elseExpr, data_def)
    else:
        if arrow.action:
            action_scope = data_def.get_childScope(arrow.action)
            type_inference_dataDef(action_scope)


def type_inference_equation(equation: SyntaxEquation, data_def: SyntaxDataDefScope):
    """
    根据句子的左值，来分配expr的返回类型值
    """
    for lhs in equation.lhs:
        if lhs == '_':
            equation.add_lhs_type(SyntaxType("any"))
        else:
            lhs_symbol = data_def.get_localVariable_InThisAndPreEnv(lhs)
            if not lhs_symbol:
                if equation.type == "emission" and data_def.have_signal_InThisAndPreEnv(lhs):
                    equation.add_lhs_type(SyntaxType("bool"))
                else:
                    raise UnknownIdentifierException(lhs)
            else:
                equation.add_lhs_type(lhs_symbol.syntaxType)
    # 现在获取了句子左值的所有类型变量，然后将他们分配给expr做推理
    type_inference_expr(equation.expr, equation.lhsTypeList, data_def)


inference_expr_handlers = {}


def inference_expr_handler(type_):
    def decorator(func):
        inference_expr_handlers[type_] = func
        return func

    return decorator


def type_inference_expr(expr: SyntaxExpr, lhs_type_list: list[SyntaxType], data_def: SyntaxDataDefScope) -> list[
    SyntaxType]:
    """根据分配的左值类型，确定每个子expr的类型，然后给出自己应该具有的返回类型
    此函数应该做到：
    1.根据输入的左值类型，确定自己的子expr应该是什么类型
    2.递归的调用此函数，向子expr分配类型
    3.收集到子expr返回的所有类型后，如果可以进一步缩小子expr的类型的范围，则再次向子expr分配类型
    4.设置自己的类型，并返回自己的类型，set_lhs_type用这个函数
    并且，如果遇到函数调用，应先对调用的函数进行类型推导
    如果遇到了模板函数，则对模板函数进行实例化，需要实例化的内容包括模板类型，size参数
    """
    _type = expr.type
    if _type in inference_expr_handlers.keys():
        handler = inference_expr_handlers[_type]
        return handler(expr, lhs_type_list, data_def)
    else:
        raise Exception(f"{expr}对应的type没用类型推导，在{data_def.get_global_name()}内")


@inference_expr_handler('Id_expr')
def type_inference_ID(expr: SyntaxExpr, lhs_type_list: list[SyntaxType], data_def: SyntaxDataDefScope):
    # 要求只能提供一个左值类型，所以需要校验
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    required_type = lhs_type_list[0]
    name = expr.objects[0]
    if expr.subType == "ID":
        expr_type = SyntaxType(tar_type='ID')  # ID 的type是ID
    elif expr.subType == "lastSinglequoteLv6id":
        name = name[1:]  # 去掉开头的'
        variable_symbol = data_def.get_localVariable_InThisAndPreEnv(name)
        expr_type = variable_symbol.syntaxType
    elif expr.subType == "Path_id":
        symbol = data_def.check_and_get_constant_param(name)
        if symbol is None:
            symbol = data_def.get_localVariable_InThisAndPreEnv(name)
        else:
            if symbol.valueExpr is not None:
                type_inference_expr(symbol.valueExpr,[symbol.syntaxType],data_def)
        expr_type = symbol.syntaxType
    else:  # SinglequoteLv6id
        expr_type = SyntaxType("bool")
    if expr_type <= required_type:
        expr.set_lhs_type([expr_type])
    else:
        raise TypeMismatchException(f"{expr}有type为{expr_type.get_real_type()}", required_type.get_real_type(), data_def)
    return expr.lhsTypeList


@inference_expr_handler('Atom')
def type_inference_Atom(expr, lhs_type_list: list[SyntaxType], data_def):
    # 要求只能提供一个左值类型，所以需要校验
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    given_type, _ = expr.get_type_and_value_for_atom()
    syntax_type = SyntaxType(given_type)
    if lhs_type_list[0] <= syntax_type:
        expr.set_lhs_type([lhs_type_list[0]])
    elif syntax_type <= lhs_type_list[0]:
        expr.set_lhs_type([syntax_type])
    else:
        raise TypeMismatchException(f"{expr}有type为{syntax_type}", lhs_type_list, data_def)
    return expr.lhsTypeList


def type_check_decorator(func):
    """类型校验装饰器，在这里进行校验，具体的函数只负责给出类型信息
    接受expr, lhs_type_list: list[SyntaxType], data_def，传递给目标函数
    收到函数返回的接受左值类型，接受右值类型，子expr列表
    把右值分给子expr，把左值和lhs_type_list进行对比。
    然后返回真正的lhs_type_list，即进行推理后得出的更精准的类型
    返回lhs_type_list
    """

    def wrapper(expr, actual_lhs_types: list[SyntaxType], data_def):
        required_lhs_types, required_rhs_types, sub_expr_list = func(expr, actual_lhs_types, data_def)
        if len(required_lhs_types) != len(actual_lhs_types) or \
                not all([a < r for a, r in zip(actual_lhs_types, required_lhs_types)]):
            raise TypeMismatchException(expr, actual_lhs_types, data_def)

        return

    return wrapper


binOp_type_table = {
    "Bool_expr": {
        "binOp": {
            "": ["bool", "bool", "bool", False]
        }
    }
}


def get_required_type_for_binOp(expr_type, expr_sub_type, binOp=""):
    sub_table = binOp_type_table.get(expr_type)
    if sub_table is None: return None
    op_table = sub_table.get(expr_sub_type)
    if op_table is None: return None
    if "" in op_table.keys():
        return op_table[""]
    return op_table.get(binOp)


def common_inference_binOp(param_list_expr: SyntaxExpr, expr_type, expr_sub_type,
                           lhs_type_list, data_def, binOp: str = ""):
    """对二元运算的普遍类型推理
    Parameters:
        param_list_expr:有两个返回值的expr，适配prefixOp的情况，其他情况需要手动捏成一个list
        need_shrink:是否需要根据expr返回值来再次进行类型推理，缩小范围
    """
    r = get_required_type_for_binOp(expr_type, expr_sub_type, binOp)
    require_types = [SyntaxType(t) for t in r[:3]]
    lhs_type = require_types[0]
    sub_types = require_types[1:3]
    if len(lhs_type_list) != 1 or not lhs_type <= lhs_type_list[0]:
        raise TypeMismatchException([lhs_type], lhs_type_list, data_def)
    actual_types = type_inference_expr(param_list_expr, sub_types, data_def)
    need_shrink = r[3]
    if need_shrink:
        min_type = min(actual_types)
        max_type = max(actual_types)
        if min_type != max_type:
            actual_types = type_inference_expr(param_list_expr, [min_type, min_type], data_def)
        # 按照更小的那个类型进行遍历，缩小范围
        if actual_types[0] != actual_types[1]:
            raise TypeMismatchException(param_list_expr, [min_type, min_type], data_def)
    return actual_types


inference_arith_handlers = {}


def inference_arith_handler(type_):
    def decorator(func):
        inference_arith_handlers[type_] = func
        return func

    return decorator


@inference_expr_handler('Arith_expr')
def type_inference_Arith(expr, lhs_type_list: list[SyntaxType], data_def):
    subtype = expr.subType
    return inference_arith_handlers[subtype](expr, lhs_type_list, data_def)


@inference_arith_handler('cast')
def type_inference_arith_cast(expr, lhs_type_list: list[SyntaxType], data_def):
    given_type = lhs_type_list[0]
    cast_type = expr.objects[1]
    if not (cast_type <= SyntaxType("numeric") or cast_type != given_type):
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    expr.set_lhs_type([cast_type])

    # 需要两边均为numeric,这边和输出没关系，只要是numeric就行，别的不管
    tar_expr = expr.objects[0]
    tar_type = type_inference_expr(tar_expr, [SyntaxType("numeric")], data_def)

    return expr.lhsTypeList


@inference_arith_handler('unary')
def type_inference_arith_unary(expr, lhs_type_list: list[SyntaxType], data_def):
    tar_expr = expr.objects[1]
    tar_type = type_inference_expr(tar_expr, lhs_type_list, data_def)
    expr.set_lhs_type(tar_type)
    # 一元运算符，将目标类型传递下去，然后将实际类型返回，没有需要修改的地方
    return expr.lhsTypeList


@inference_arith_handler('binOp')
def type_inference_arith_binOp(expr, lhs_type_list: list[SyntaxType], data_def):
    # binOp会根据不同的二元运算符给出不同的要求
    # lnot, land, lor, lxor 是两个unsigned，需求且输出unsigned
    # lsl ,lsr 第一个是unsigned，第二个是integer，需求且输出unsigned
    # 其他情况则与输入类型相同
    # 是最宽泛的类型需求，对非移位运算的情况，若子式发现可以更具体的话则要根据具体的类型再遍历一遍
    bitwiseOp = {'lnot', 'land', 'lor', 'lxor'}
    shiftOp = {'lsl', 'lsr'}
    op = expr.objects[1]
    given_type = lhs_type_list[0]

    if op in bitwiseOp:
        required_given_type = SyntaxType("unsigned")
        min_type = min([required_given_type, given_type])
        first_type = min_type
        second_type = min_type
    elif op in shiftOp:
        required_given_type = SyntaxType("unsigned")
        min_type = min([required_given_type, given_type])
        first_type = min_type
        second_type = SyntaxType("integer")
    else:
        required_given_type = SyntaxType("numeric")
        min_type = min([required_given_type, given_type])
        first_type = min_type
        second_type = min_type
    # if not required_given_type<=given_type:
    #     raise TypeMismatchException(expr, lhs_type_list, data_def)
    given_first_type = type_inference_expr(expr.objects[0], [first_type], data_def)[0]
    given_second_type = type_inference_expr(expr.objects[2], [second_type], data_def)[0]
    if op not in shiftOp:
        # 非移位运算
        if given_first_type < given_second_type:
            given_second_type = type_inference_expr(expr.objects[2], [given_first_type], data_def)[0]
        elif given_second_type < given_first_type:
            given_first_type = type_inference_expr(expr.objects[0], [given_second_type], data_def)[0]
        # 按照更小的那个类型进行遍历，缩小范围
        if not given_first_type == given_second_type:
            raise TypeMismatchException(expr, required_given_type, data_def)
    expr.set_lhs_type([given_first_type])
    # 第一个子表达式，即左侧的那个表达式不管是什么操作符都是要返回的那个
    return expr.lhsTypeList


@inference_expr_handler('Relation_expr')
def type_inference_Relation(expr, lhs_type_list: list[SyntaxType], data_def):
    # =与<>不对子类型做限制
    # 其他情况，则限制为numeric
    # 两侧的类型必须一致
    # 返回类型肯定是bool，不用讨论
    if len(lhs_type_list) != 1 and lhs_type_list[0] != SyntaxType('bool'):
        raise TypeMismatchException(expr, lhs_type_list, data_def)

    op = expr.objects[1]
    if op == "=" or op == "<>":
        required_type = SyntaxType("any")
    else:
        required_type = SyntaxType("numeric")
    given_first_type = type_inference_expr(expr.objects[0], [required_type], data_def)[0]
    given_second_type = type_inference_expr(expr.objects[2], [required_type], data_def)[0]
    if given_first_type < given_second_type:
        given_second_type = type_inference_expr(expr.objects[2], [given_first_type], data_def)
    elif given_second_type < given_first_type:
        given_first_type = type_inference_expr(expr.objects[0], [given_second_type], data_def)
    # 按照更小的那个类型进行遍历，缩小范围
    if given_first_type != given_second_type:
        raise TypeMismatchException(expr, given_second_type, data_def)

    expr.set_lhs_type([SyntaxType('bool')])
    return expr.lhsTypeList


@inference_expr_handler('Bool_expr')
def type_inference_Bool(expr, lhs_type_list: list[SyntaxType], data_def):
    """布尔运算，要求都是bool类型"""
    # 需求类型bool，子运算类型bool，很简单
    # packed_sub_expr = SyntaxExpr(type="List_expr", subtype="List_expr", scope=data_def,
    #                              objects=[expr.objects[0], expr.objects[2]], returnNum=2)
    required_type = SyntaxType("bool")
    if len(lhs_type_list) != 1 and lhs_type_list[0] != required_type:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    sub_type = expr.subType

    if sub_type == "NOT":
        type_inference_expr(expr.objects[0], [required_type], data_def)
    elif sub_type == "binOp":
        type_inference_expr(expr.objects[0], [required_type], data_def)
        type_inference_expr(expr.objects[2], [required_type], data_def)
    else:  # hashtag
        for sub_expr in expr.objects[0]:
            type_inference_expr(sub_expr, [required_type], data_def)
    expr.set_lhs_type([required_type])
    return expr.lhsTypeList


inference_tempo_handlers = {}


def inference_tempo_handler(type_):
    def decorator(func):
        inference_tempo_handlers[type_] = func
        return func

    return decorator


@inference_expr_handler('Tempo_expr')
def type_inference_tempo(expr, lhs_type_list: list[SyntaxType], data_def):
    subtype = expr.subType
    handler = inference_tempo_handlers.get(subtype)
    if handler is None:
        raise Exception(f"tempo的{subtype}没实现")
    return handler(expr, lhs_type_list, data_def)


def type_inference_on_groups(sub_exprs: list[SyntaxExpr], lhs_type_list_on_each, data_def):
    # 处理可以多返回的操作符
    given_type_lists = [type_inference_expr(sub_expr, lhs_type_list_on_each, data_def) for sub_expr in sub_exprs]
    # 他们返回的长度一定相等
    actual_types = list(map(min, zip(*given_type_lists)))
    for i, given_types in enumerate(given_type_lists):
        for g, a in zip(given_types, actual_types):
            if g < a:
                type_inference_expr(sub_exprs[i], actual_types, data_def)
                break
    return actual_types


@inference_tempo_handler("ARROW")
def type_inference_tempo_arrow(expr, lhs_type_list: list[SyntaxType], data_def):
    # arrow可以同时处理多个变量
    actual_types = type_inference_on_groups([expr.objects[0], expr.objects[1]], lhs_type_list, data_def)
    expr.set_lhs_type(actual_types)
    return expr.lhsTypeList


@inference_tempo_handler("FBY")
def type_inference_tempo_fby(expr, lhs_type_list: list[SyntaxType], data_def):
    # 和pre预算非常的相似
    actual_types = type_inference_on_groups([expr.objects[0], expr.objects[2]], lhs_type_list, data_def)
    expr.set_lhs_type(actual_types)
    return expr.lhsTypeList


@inference_tempo_handler("PRE")
def type_inference_tempo_pre(expr, lhs_type_list: list[SyntaxType], data_def):
    expr.set_lhs_type(type_inference_expr(expr.objects[0], lhs_type_list, data_def))
    return expr.lhsTypeList


@inference_tempo_handler("TIMES")
def type_inference_tempo_times(expr, lhs_type_list: list[SyntaxType], data_def):
    # 需要bool类型，子类型分别是signed和bool
    # 不支持列表
    if len(lhs_type_list) != 1 or lhs_type_list[0] != SyntaxType("bool"):
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    type_inference_expr(expr.objects[0], [SyntaxType("signed")], data_def)
    type_inference_expr(expr.objects[1], [SyntaxType("bool")], data_def)
    expr.set_lhs_type(lhs_type_list)
    return expr.lhsTypeList


inference_array_handlers = {}


def inference_array_handler(type_):
    def decorator(func):
        inference_array_handlers[type_] = func
        return func

    return decorator


@inference_expr_handler("Array_expr")
def type_inference_array(expr, lhs_type_list: list[SyntaxType], data_def):
    subtype = expr.subType
    handler = inference_array_handlers.get(subtype)
    if handler is None:
        raise Exception(f"array的{subtype}没实现")
    handler(expr, lhs_type_list, data_def)


@inference_array_handler("construct")
def type_inference_array_construct(expr, lhs_type_list: list[SyntaxType], data_def):
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    required_type = lhs_type_list[0]
    given_element_type = type_inference_expr(expr.objects[0], [required_type.get_element_type_for_array()], data_def)[0]
    given_array_length = cal_const_expr(expr.objects[1], SyntaxType("integer"), data_def).value
    # 也有可能数组长度只有最小值限制
    if not (given_array_length == required_type.get_size() or given_array_length > required_type.min_size):
        raise UnsatisfiableSizeException(expr, given_array_length,
                                         f"{required_type.get_size()}或最小值{required_type.min_size}")

    given_type = SyntaxType(tar_type="array", scope=data_def)
    given_type.set_element_and_size(given_element_type, given_array_length)
    expr.set_lhs_type([given_type])
    return expr.lhsTypeList


@inference_array_handler("get")
def type_inference_array_get(expr, lhs_type_list: list[SyntaxType], data_def):
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    idx_symbol = cal_const_expr(expr.objects[1], SyntaxType("integer"), data_def)
    # if idx_symbol.type!=SyntaxType("integer"):
    #     raise TypeMismatchException(expr.objects[1], idx_symbol.type, data_def)
    required_type = lhs_type_list[0]
    idx_value = idx_symbol.value
    expr.idx_list.append(idx_value)

    required_arr_type = SyntaxType("array", scope=data_def).set_element_and_size(required_type, 0)
    required_arr_type.min_size = idx_value
    given_arr_type: SyntaxType = type_inference_expr(expr.objects[0], [required_arr_type], data_def)[0]

    expr.set_lhs_type([given_arr_type.arrayType])
    return expr.lhsTypeList


@inference_array_handler("slice")
def type_inference_array_slice(expr, lhs_type_list: list[SyntaxType], data_def):
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)

    idx_symbols = [cal_const_expr(expr.objects[1], SyntaxType("integer"), data_def),
                   cal_const_expr(expr.objects[2], SyntaxType("integer"), data_def)]
    for i, idx_symbol in enumerate(idx_symbols):
        # if idx_symbol.type!=SyntaxType("integer"):
        #     raise TypeMismatchException(expr.objects[i], idx_symbol.type, data_def)
        idx_value = idx_symbol.value
        expr.idx_list.append(idx_value)

    required_arr_type = SyntaxType("array", scope=data_def).set_element_and_size(lhs_type_list[0], 0)
    required_arr_type.min_size = idx_symbols[1].value
    given_arr_type: SyntaxType = type_inference_expr(expr.objects[0], [required_arr_type], data_def)[0]

    actual_returned_type = SyntaxType("array", scope=data_def).set_element_and_size(given_arr_type.arrayType,
                                                                                    idx_symbols[1].value - idx_symbols[
                                                                                        0].value)
    expr.set_lhs_type([actual_returned_type])
    return expr.lhsTypeList


@inference_array_handler("getdefault")
def type_inference_array_get_default(expr, lhs_type_list: list[SyntaxType], data_def):
    # 是一个动态取数的操作，所以不用静态获取下标
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    required_type = lhs_type_list[0]

    # 先校验一下下标部分的表达式
    idx_exprs = expr.objects[1]
    required_arr_type = required_type
    for idx_expr in idx_exprs:
        type_inference_expr(idx_expr, [SyntaxType("integer")], data_def)
        # 逐层去构建一个给被取数表达式的对应类型
        # 对大小完全没要求，因为不知道到底是一个什么情况
        required_arr_type = SyntaxType("array", scope=data_def).set_element_and_size(required_arr_type, 0)
        required_arr_type.min_size = 0

    def get_element_type_recursive(arr_type: SyntaxType, depth):
        """递归获取元素类型"""
        cur_type = arr_type
        for i in range(depth):
            cur_type = cur_type.arrayType
        return cur_type

    def build_arr_type(element_type: SyntaxType, depth):
        """再根据元素类型填充成数组,对长度没有要求"""
        output: SyntaxType = element_type
        for i in range(depth):
            output = SyntaxType("array").set_element_and_size(output, 0)
            output.min_size = 0
        return output

    # 然后拿这个新得到的类型去推断被取数表达式
    given_arr_type = type_inference_expr(expr.objects[0], [required_arr_type], data_def)[0]
    given_element_type = get_element_type_recursive(given_arr_type, len(idx_exprs))
    # 用提供的类型去推断默认表达式
    given_default_type = type_inference_expr(expr.objects[2], [required_type], data_def)[0]

    if given_element_type < given_default_type:
        given_default_type = type_inference_expr(expr.objects[2], [given_element_type], data_def)[0]
    elif given_default_type < given_element_type:
        given_arr_type = type_inference_expr(expr.objects[0], [build_arr_type(given_default_type, len(idx_exprs))],
                                             data_def)

    expr.set_lhs_type([given_default_type])
    return expr.lhsTypeList


@inference_array_handler("list")
def type_inference_array_list(expr, lhs_type_list: list[SyntaxType], data_def):
    # 构造函数，允许output:int32^4;然后output=[(1,2),(3,4)];实在是太抽象了
    # 还好准备了returnNum属性用来处理list的情况
    if len(lhs_type_list) != 1:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    required_type = lhs_type_list[0]
    elements: list[SyntaxExpr] = expr.objects[0].objects[0]
    return_sum = sum([element.returnNum for element in elements])
    if not (required_type.get_size() == return_sum or required_type.min_size < return_sum):
        UnsatisfiableSizeException(expr, required_type.get_size(),
                                   f"{required_type.get_size()}或最小值{required_type.min_size}")

    # 然后把子类型都分发下去
    # 为什么我之前不这么做？？？？太愚蠢了，明明直接把list_expr拆开就好了
    # 不过无需考虑list_expr的嵌套格式还是不错的
    element_exprs = list()
    for element in elements:
        if element.type == "List_expr":
            element_exprs.extend(element.objects)
        else:
            element_exprs.append(element)
    actual_element_type = \
    type_inference_on_groups(element_exprs, [required_type.get_element_type_for_array()], data_def)[0]
    expr.set_lhs_type([SyntaxType("array",scope=data_def).set_element_and_size(actual_element_type, required_type.get_size())])
    return expr.lhsTypeList


@inference_expr_handler("Switch_expr")
def type_inference_switch(expr, lhs_type_list: list[SyntaxType], data_def):
    sub_type = expr.subType
    if sub_type == "IF":
        actual_types = type_inference_on_groups(expr.objects[1:], lhs_type_list, data_def)
        type_inference_expr(expr.objects[0], [SyntaxType("bool")], data_def)
        expr.set_lhs_type(actual_types)
        return expr.lhsTypeList
    else:
        raise Exception("switch的case语句还没实现推导")


@inference_expr_handler('List_expr')
def type_inference_List(expr, lhs_type_list: list[SyntaxType], data_def):
    # 需要每个表达式在后处理哪里先记一下自己返回多少个变量，可恶
    # ↑做好了，比想象的简单很多，大部分expr只接受一个输出
    # 然后根据子表达式的返回变量情况，把输入的变量类型发送下去做校验
    expr_list = expr.objects[0]
    cur_index = 0
    actual_type_list = list()
    for sub_expr in expr_list:
        expect_num = sub_expr.returnNum
        actual_type = type_inference_expr(sub_expr, lhs_type_list[cur_index:cur_index + expect_num], data_def)
        actual_type_list.extend(actual_type)
        cur_index += expect_num
    expr.set_lhs_type(actual_type_list)
    return expr.lhsTypeList


inference_operator_handlers = {}


def inference_operator_handler(type_):
    def decorator(func):
        inference_operator_handlers[type_] = func
        return func

    return decorator


def type_inference_operator(operator, lhs_type_list, param_expr, data_def) -> (
list[int], SyntaxUserOp or None, list[SyntaxType]):
    """让所有的operator处理函数返回一个列表，涵盖了到目前为止所构建的上下文数组的情况，不用数组就返回空列表
    让apply_expr那边进行处理
    比如map (map <<3>>) <<2>> 返回[2,3]
    直接调用函数就返回[]
    所以共返回三个参数
    调用上下文的数组，调用的函数（无则None），和左值列表
    """
    handler = inference_operator_handlers.get(operator.subtype)
    if handler is None:
        raise Exception(f"不对,{operator.subtype}还没实现")

    return handler(operator, lhs_type_list, param_expr, data_def)


@inference_expr_handler("Apply_expr")
def type_inference_Apply(expr, lhs_type_list: list[SyntaxType], data_def):
    # 设置这个expr函数调用情况，即对调用函数封装的层次，用于outC中
    # 以一个字典的形式保存，map( map func<<3>>)<<2>> 得到的字典是{func:[2,3]}
    # 需要根据具体的调用情况，来确认参数的具体类型
    # 所以不能把参数传给operator，因为是没用的，iterator等会改变参数的格式，考虑到参数内可能有多返回值的情况，无法简单构造函数
    # 应该对参数进行类型校验，而非对op进行校验
    # 但是也需要考虑到模板函数实例化的情况，此时operator无法得知具体需求的类型

    # 让operator处理函数返回此op返回的左值，和需求的右值的类型，让apply_expr这边进行校验
    # 如果为模板函数则单独进行判断
    param_expr = expr.objects[1]
    operator = expr.objects[0]
    context_list, apply_userOp, actual_lhs_type = type_inference_operator(operator, lhs_type_list, param_expr, data_def)

    if apply_userOp is not None:
        expr.add_applied_Op(apply_userOp, context_list)
        add_apply_expr_to_state_and_op(data_def, expr)
    expr.set_lhs_type(actual_lhs_type)
    return expr.lhsTypeList


def add_apply_expr_to_state_and_op(data_def: SyntaxDataDefScope, expr):
    """向这个作用域上层的state与op作用域添加这个函数调用表达式"""
    cur_scope = data_def
    while cur_scope.type != "package":
        if isinstance(cur_scope, SyntaxUserOp) or isinstance(cur_scope, SyntaxState):
            cur_scope.apply_exprs.append(expr)
        cur_scope = cur_scope.prevScope


@inference_expr_handler("generalized_get")
def type_inerence_generalized_get(expr, lhs_type_list: list[SyntaxType], data_def):
    """给iterator等表达式使用，要求expr为数组，对其进行抽象的取数操作，即int[]变为int，可以对多返回值也生效"""
    # 组建对下层表达式需要的左值类型,获取lhs作为数组元素的类型
    sub_lhs_list = []
    array_size = expr.objects[1]
    map_index = expr.objects[2]
    if map_index < 0 or map_index >= len(lhs_type_list):
        raise Exception(f"不对，{map_index}>{lhs_type_list}的长度了")
    for i in range(len(lhs_type_list)):
        lhs = lhs_type_list[i]
        if i < map_index:
            sub_lhs_list.append(lhs)
        else:
            sub_lhs = SyntaxType(tar_type="array", scope=data_def)
            sub_lhs.set_element_and_size(lhs, array_size)
            sub_lhs_list.append(sub_lhs)

    actual_type_list = type_inference_expr(expr.objects[0], sub_lhs_list, data_def)
    expr.set_lhs_type(actual_type_list)
    return expr.lhsTypeList


@inference_operator_handler("activateDefault")
def type_inference_apply_activateDefault(operator: SyntaxOperator, lhs_type_list: list[SyntaxType], param_expr,
                                         data_def):
    # 三个组件，一个op，一个bool表达式，一个默认表达式
    type_inference_expr(operator.objects[1], [SyntaxType("bool")], data_def)
    default_types = type_inference_expr(operator.objects[2], lhs_type_list, data_def)
    op_context_list, apply_userOp, op_types = type_inference_operator(operator.objects[0], lhs_type_list, param_expr,
                                                                      data_def)
    min_types = [min(a, b) for a, b in zip(default_types, op_types)]

    if not all([a == b for a, b in zip(default_types, min_types)]):
        type_inference_expr(operator.objects[2], min_types, data_def)
    if not all([a == b for a, b in zip(op_types, min_types)]):
        op_context_list, apply_userOp, op_types = type_inference_operator(operator.objects[0], min_types, param_expr,
                                                                          data_def)

    operator.set_lhs_type(op_types)
    return op_context_list, apply_userOp, operator.lhsTypeList


@inference_operator_handler("make")
def type_inference_apply_make(operator: SyntaxOperator, lhs_type_list: list[SyntaxType], param_expr,
                              data_def: SyntaxDataDefScope):
    # 先找到对应的结构体，然后再进行校验
    struct_type: SyntaxType = data_def.check_and_get_type_symbol(operator.objects[0]).syntaxType
    required_type = lhs_type_list[0]

    if len(lhs_type_list) != 1 or required_type != struct_type or struct_type.get_real_type().type != "field_decl":
        raise TypeMismatchException(operator, lhs_type_list, data_def)

    fields = struct_type.get_real_type().fields
    given_types: list[SyntaxType] = [field.syntaxType for field in fields]
    type_inference_expr(param_expr, given_types, data_def)

    operator.set_lhs_type([struct_type])
    return [], None, operator.lhsTypeList


@inference_operator_handler("flatten")
def type_inference_apply_flatten(operator: SyntaxOperator, lhs_type_list: list[SyntaxType], param_expr, data_def):
    # 参数表达式为operator明确给出的类型
    struct_type: SyntaxType = data_def.check_and_get_type_symbol(operator.objects[0]).syntaxType
    type_inference_expr(param_expr, [struct_type], data_def)

    fields = struct_type.get_real_type().fields
    given_types: list[SyntaxType] = [field.syntaxType for field in fields]
    # 返回的左值类型为对给出的类型进行解包
    # 然后比较给出的左值类型和参数中要求的左值类型

    if len(given_types) != len(lhs_type_list) or not all(g <= r for g, r in zip(given_types, lhs_type_list)):
        raise TypeMismatchException(operator, lhs_type_list, data_def)

    operator.set_lhs_type(given_types)
    return [], None, operator.lhsTypeList


@inference_operator_handler("iterator")
def type_inference_apply_iterator(operator: SyntaxOperator, lhs_type_list: list[SyntaxType], param_expr, data_def):
    """
    map,fold,mapi,foldi,mapfold,mapfoldi
    """
    # 先就map和fold，把abc_N做完了再说别的
    # 加入带i的情况，需要给下层operator的最前面塞一个int32类型的参数
    sub_operator = operator.objects[2]
    required_length = cal_const_expr(operator.objects[3], SyntaxType("integer"), data_def).value
    operator.set_array_length(required_length)
    iterator_op: str = operator.objects[0]
    if iterator_op.startswith("mapfold"):
        map_index = operator.objects[1]
    elif iterator_op.startswith("map"):
        map_index = 0
    else:
        # iterator_op.startswith("fold")
        map_index = 1
    # 根据不同算符，进行推理
    non_map_lhs_list = lhs_type_list[:map_index]
    map_lhs_list = lhs_type_list[map_index:]
    for lhs in map_lhs_list:
        if lhs.get_size() != required_length:
            raise TypeMismatchException(lhs, f"尺寸为{required_length}的数组", data_def)
    required_lhs_types = non_map_lhs_list + [lhs.get_element_type_for_array() for lhs in map_lhs_list]

    required_param = SyntaxExpr(type="generalized_get", subtype="", scope=data_def,
                                objects=[param_expr, required_length, map_index], returnNum=param_expr.returnNum)
    # 构造一个新的参数expr，给下一层operator使用
    if iterator_op.endswith("i"):
        # 如果带了i要塞参数
        # 随便加一个能过就行
        tmp_idx_expr = SyntaxExpr(type="Atom", subtype="integernum", scope=data_def, objects=["1"])
        required_param = SyntaxExpr(type="List_expr", subtype="List_expr", scope=data_def,
                                    objects=[[tmp_idx_expr, required_param]], returnNum=required_param.returnNum + 1)

    context_list, apply_userOp, given_lhs_list = type_inference_operator(sub_operator, required_lhs_types,
                                                                         required_param, data_def)
    if iterator_op.startswith("fold"):
        # 只返回第一个
        actual_lhs_list = [given_lhs_list[0]]
    else:
        # 拿到下层推理后的真实类型，再包装后返还
        given_non_map = given_lhs_list[:map_index]
        given_map = given_lhs_list[map_index:]
        actual_lhs_list = given_non_map + [SyntaxType(tar_type="array").set_element_and_size(t, required_length)
                                           for t in given_map]
    operator.set_lhs_type(actual_lhs_list)
    context_list.insert(0, required_length)
    return context_list, apply_userOp, actual_lhs_list


@inference_operator_handler("PREFIXOP")
def type_inference_apply_prefixOp(operator: SyntaxOperator, lhs_type_list: list[SyntaxType], param_expr, data_def):
    """通过prefixop获取对应的校验格式，与对应的expr是等价的"""
    corres_typs = None
    prefixOp = operator.objects[0]
    for key_set, types in SyntaxOperator.prefix_op_2_expr_dict.items():
        if prefixOp in key_set:
            corres_typs = types
            break
    equivalent_expr = SyntaxExpr(type=corres_typs[0], subtype=corres_typs[1], scope=data_def)
    # 然后向equivalent_expr内部填入对应的object
    # 这里直接让expr那边做校验，开摆了
    # 最终的目的是对param_expr进行推导
    if equivalent_expr.subType == "unary":
        # 单目运算，直接把操作符放进去然后交给对应表达式
        # 这样就完成了对参数表达式的类型推导工作了
        equivalent_expr.add_object(prefixOp.replace("$", ""))
        equivalent_expr.add_object(param_expr)
        actual_lhs_list = type_inference_expr(equivalent_expr, lhs_type_list, data_def)
    else:
        actual_lhs_list = common_inference_binOp(param_expr, corres_typs[0], corres_typs[1], lhs_type_list, data_def,
                                                 prefixOp.replace("$", ""))
    operator.set_lhs_type(actual_lhs_list)
    return [], None, actual_lhs_list


@inference_operator_handler("Path_id")
def type_inference_apply_path_id(operator: SyntaxOperator, lhs_type_list: list[SyntaxType], param_expr, data_def):
    tar_userOp = operator.appliedUserOp
    # 校验一下，要求的类型是不是和目标op返回的类型一样
    # 这里有可能左值类型并非基本类型，所以仅当可以推断出来一个基本类型时才去进行实例化操作
    input_types = [param.syntaxType for param in tar_userOp.inParams]
    type_inference_expr(param_expr, input_types, data_def)
    # 检查并进行模板实例化
    if tar_userOp.isTemplate():
        tar_userOp = instantiate_template_function(tar_userOp, param_expr.lhsTypeList, input_types, param_expr,
                                                   operator.objects[1])
        operator.appliedUserOp = tar_userOp
        # 实例化后再推理一边，因为实例化后函数的输入参数类型变了
        input_types = [param.syntaxType for param in tar_userOp.inParams]
        type_inference_expr(param_expr, input_types, data_def)

    returned_types = [param.syntaxType for param in tar_userOp.outParams]
    if not all(g <= r for g, r in zip(returned_types, lhs_type_list)):
        raise TypeMismatchException(f"{tar_userOp.get_global_name()}有type{returned_types}", lhs_type_list, data_def)

    type_inference_userOp(tar_userOp)
    operator.set_lhs_type(returned_types)
    return [], tar_userOp, returned_types


def instantiate_template_function(userOp: SyntaxUserOp, lhs_type_list: list[SyntaxType], op_input_types, param_expr,
                                  size_exprs):
    """模板函数实例化，复制一个函数，并修改各种类型"""
    # 首先需要检查是否所有模板都可以确定类型
    print(f"对{userOp.get_global_name()}进行模板函数实例化")
    instantiate_dict = dict()
    for given_type, required_type in zip(lhs_type_list, op_input_types):
        # 逐个把左值类型和op输入参数的类型做对比
        if required_type.type != "typevar": continue
        template_var = required_type.value
        if not template_var in instantiate_dict.keys():
            instantiate_dict[template_var] = given_type
            continue
        # 确保是最精确的那个类型
        pre_given_type = instantiate_dict[template_var]
        if given_type <= pre_given_type:
            instantiate_dict[template_var] = given_type
        elif not pre_given_type <= given_type:
            # 如果左不<=右，右不<=左，说明无法进行推导了
            raise CanNotInstantiateException(userOp, param_expr, "参数类型推导冲突")

    # 如果长度不一样，说明不是所有模板参数都在输入参数中提及
    if len(instantiate_dict) != len(userOp.typeVarSymbolTable):
        raise CanNotInstantiateException(userOp, param_expr, "有模板参数并未在输入参数中涉及")
    if not all(t.is_basic_type() for t in instantiate_dict.values()):
        raise CanNotInstantiateException(userOp, param_expr, "有模板参数无法推导为基本类型")
    print(f"获取的实例化字典为:{instantiate_dict}")

    instantiate_sizes = list()
    for size_expr, size_param in zip(size_exprs, userOp.sizeParams):
        const_value = cal_const_expr(size_expr, SyntaxType('unsigned'), userOp)
        instantiate_sizes.append(const_value)

    if (instantiated_op := get_instantiated_op(userOp, instantiate_dict, instantiate_sizes)) is not None:
        # 神必海象运算符
        # 一点也不好使
        print(f"已经生成过对应的实例化函数{instantiated_op.name}")
        return instantiated_op
    # 然后需要复制一份原函数，并把它修改以达到实例化的目的
    # 修改名字，和类型变量声明
    instantiate_userOp = deepcopy_userOp(userOp)
    for name in instantiate_userOp.typeVarSymbolTable.keys():
        type_symbol = instantiate_userOp.typeVarSymbolTable[name]
        type_symbol.syntaxType = instantiate_dict[name]

    for size_symbol, size_param in zip(instantiate_sizes, instantiate_userOp.sizeParams):
        size_param.set_value(size_symbol.value)
        size_param.syntaxType = size_symbol.type

    if len(size_exprs) != len(instantiate_userOp.sizeParams):
        raise CanNotInstantiateException(instantiate_userOp, size_exprs, "输入的sizedecl长度与函数声明的不一样")

    instantiate_userOp.name = generate_instantiate_name(userOp, instantiate_dict, instantiate_sizes)
    instantiate_userOp.get_my_package().add_userOp(instantiate_userOp)
    print(f"生成实例化函数{instantiate_userOp.get_global_name()}")
    add_instantiated_op(userOp, instantiate_dict, instantiate_sizes, instantiate_userOp)
    return instantiate_userOp


instantiated_op_dict: dict[SyntaxUserOp, list[list[dict[str, SyntaxType], list[ConstValue], SyntaxUserOp]]] = dict()


# 类型有点太长了
def get_instantiated_op(userOp, instantiate_dict, instantiate_sizes) -> SyntaxUserOp or None:
    """找一下是否有已经实例化的op"""
    instantiated_ops = instantiated_op_dict.get(userOp)
    if instantiated_ops is None:
        instantiated_op_dict[userOp] = list()
        return None
    for instantiated_list in instantiated_ops:
        _dict, sizes, op = instantiated_list[0], instantiated_list[1], instantiated_list[2]
        if _dict == instantiate_dict and sizes == instantiate_sizes:
            return op
    return None


def add_instantiated_op(userOp, instantiate_dict, instantiate_sizes, instantiated_op) -> None:
    instantiated_op_dict.get(userOp).append([instantiate_dict, instantiate_sizes, instantiated_op])


def generate_instantiate_name(userOp, instantiate_dict, instantiate_sizes):
    """不能重名，生成func_int32之类的名字"""

    post_fix = "_".join(t.get_real_type().type for t in instantiate_dict.values())
    if userOp.isImported:
        instant_name = f"{userOp.name}{post_fix[-2:]}"
    else:
        if instantiate_sizes:
            post_fix += "_" + "_".join(str(s.value) for s in instantiate_sizes)
        instant_name = f"{userOp.name}_{post_fix}"
    package = userOp.get_my_package()
    if package.get_userOp(instant_name) is None:
        return instant_name

    # 如果有占用就生成新名字
    count = 1
    while True:
        instant_name = f"{userOp.name}_{str(count)}_{post_fix}"
        if package.get_userOp(instant_name) is None:
            return instant_name
        count += 1


def deepcopy_userOp(userOp):
    """天才"""
    tmp_prev_scope = userOp.prevScope
    userOp.prevScope = None
    copied_userOp = copy.deepcopy(userOp)
    userOp.prevScope = tmp_prev_scope
    copied_userOp.prevScope = tmp_prev_scope
    return copied_userOp
