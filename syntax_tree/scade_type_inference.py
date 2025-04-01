from syntax_tree.SyntaxClass import *


def type_inference(main_operator:SyntaxUserOp):
    """对拓扑排序后，从后向前遍历userOP，进行类型推导
    有主节点的存在，最末端的userOp一定是主节点，且不是模板方法
    进行类型推导，与函数实例化操作
    从主节点开始向下遍历可以保证不会遇到模板类型的比较的情况
    """
    type_inference_userOp(main_operator)

def type_inference_userOp(userOp:SyntaxUserOp):
    """
    类型推导，如果是模板函数要实例化，遍历的时候靠调用的path来找下一个目标函数
    """
    for equation in userOp.equations:
        type_inference_equation(equation,userOp)

def type_inference_equation(equation:SyntaxEquation,data_def:SyntaxDataDefScope):
    """
    根据句子的左值，来分配expr的返回类型值
    """
    for lhs in equation.lhs:
        lhs_symbol = data_def.get_localVariable_InThisAndPreEnv(lhs)
        if not lhs_symbol:
            raise UnknownIdentifierException(lhs_symbol)
        equation.add_lhs_type(lhs_symbol.syntaxType)
    # 现在获取了句子左值的所有类型变量，然后将他们分配给expr做推理
    type_inference_expr(equation.expr,equation.lhsTypeList,data_def)


inference_expr_handlers = {}


def inference_expr_handler(type_):
    def decorator(func):
        inference_expr_handlers[type_] = func
        return func

    return decorator

def type_inference_expr(expr:SyntaxExpr,lhs_type_list:list[SyntaxType],data_def:SyntaxDataDefScope)->list[SyntaxType]:
    """根据分配的左值类型，确定每个子expr的类型，然后给出自己应该具有的返回类型
    此函数应该做到：
    1.根据输入的左值类型，确定自己的子expr应该是什么类型
    2.递归的调用此函数，向子expr分配类型
    3.收集到子expr返回的所有类型后，如果可以进一步缩小子expr的类型的范围，则再次向子expr分配类型
    4.设置自己的类型，并返回自己的类型，set_lhs_type用这个函数
    并且，如果遇到函数调用，应先对调用的函数进行类型推导
    如果遇到了模板函数，则对模板函数进行实例化，需要实例化的内容包括模板类型，size参数
    """
    _type=expr.type
    handler=inference_expr_handlers[_type]
    return handler(expr,data_def,lhs_type_list)

@inference_expr_handler('Id_expr')
def type_inference_ID(expr:SyntaxExpr,data_def:SyntaxDataDefScope,lhs_type_list:list[SyntaxType]):
    # 要求只能提供一个左值类型，所以需要校验
    if len(lhs_type_list)!=1:
        raise TypeMismatchException(expr,lhs_type_list,data_def)
    required_type=lhs_type_list[0]
    if expr.subType == "ID" :
        expr_type=SyntaxType(type='ID')# ID 的type是ID
    elif expr.subType == "lastSinglequoteLv6id":
        expr_type=expr.syntaxSymbol.syntaxType
    elif expr.subType == "Path_id":
        expr_type=expr.syntaxSymbol.syntaxType
    else: # SinglequoteLv6id
        expr_type=SyntaxType("bool")
    if expr_type <= required_type:
        expr.set_lhs_type([expr_type])
    else:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    return lhs_type_list

@inference_expr_handler('Atom')
def type_inference_Atom(expr, lhs_type_list:list[SyntaxType],data_def):
    # 要求只能提供一个左值类型，所以需要校验
    if len(lhs_type_list)!=1:
        raise TypeMismatchException(expr,lhs_type_list,data_def)
    given_type,_=get_type_and_value_for_atom(expr)
    syntax_type=SyntaxType(given_type)
    if syntax_type <= lhs_type_list[0]:
        expr.set_lhs_type([syntax_type])
    else:
        raise TypeMismatchException(expr, lhs_type_list, data_def)
    return [syntax_type]

inference_arith_handlers={}
def inference_arith_handler(type_):
    def decorator(func):
        inference_arith_handlers[type_] = func
        return func

    return decorator
@inference_expr_handler('Arith_expr')
def type_inference_Arith(expr, lhs_type_list:list[SyntaxType],data_def):
    if len(lhs_type_list)!=1 or not lhs_type_list[0]<=SyntaxType('numeric'):
        raise TypeMismatchException(expr,lhs_type_list,data_def)
    subtype=expr.subType
    return inference_arith_handlers[subtype](expr,lhs_type_list,data_def)

@inference_arith_handler('cast')
def type_inference_arith_cast(expr, lhs_type_list:list[SyntaxType],data_def):
    given_type = lhs_type_list[0]
    cast_type=expr.objects[1]
    if not (cast_type <= SyntaxType("numeric") or cast_type != given_type):
        raise TypeMismatchException(expr,lhs_type_list,data_def)
    expr.set_lhs_type([cast_type])

    # 需要两边均为numeric,这边和输出没关系，只要是numeric就行，别的不管
    tar_expr=expr.objects[0]
    tar_type=type_inference_expr(tar_expr,[SyntaxType("numeric")],data_def)

    return expr.lhsTypeList

@inference_arith_handler('unary')
def type_inference_arith_unary(expr, lhs_type_list:list[SyntaxType],data_def):
    tar_expr=expr.objects[0]
    tar_type=type_inference_expr(tar_expr,lhs_type_list,data_def)
    expr.set_lhs_type([tar_type])
    # 一元运算符，将目标类型传递下去，然后将实际类型返回，没有需要修改的地方
    return expr.lhsTypeList

@inference_arith_handler('binOp')
def type_inference_arith_binOp(expr, lhs_type_list:list[SyntaxType],data_def):
    # binOp会根据不同的二元运算符给出不同的要求
    # lnot, land, lor, lxor 是两个unsigned，需求且输出unsigned
    # lsl ,lsr 第一个是unsigned，第二个是integer，需求且输出unsigned
    # 其他情况则与输入类型相同
    # 是最宽泛的类型需求，对非移位运算的情况，若子式发现可以更具体的话则要根据具体的类型再遍历一遍
    bitwiseOp={'lnot','land','lor','lxor'}
    shiftOp={'lsl','lsr'}
    op=expr.objects[1]
    if op in bitwiseOp:
        required_given_type=SyntaxType("unsigned")
        first_type=SyntaxType("unsigned")
        second_type=SyntaxType("unsigned")
    elif op in shiftOp:
        required_given_type = SyntaxType("unsigned")
        first_type = SyntaxType("unsigned")
        second_type = SyntaxType("integer")
    else:
        required_given_type = SyntaxType("numeric")
        first_type = SyntaxType("numeric")
        second_type = SyntaxType("numeric")
    given_type = lhs_type_list[0]
    if not given_type <= required_given_type:
        raise TypeMismatchException(expr,lhs_type_list,data_def)
    given_first_type = type_inference_expr(expr.objects[0],[first_type],data_def)[0]
    given_second_type = type_inference_expr(expr.objects[2],[second_type],data_def)[0]
    if op not in shiftOp:
        # 非移位运算
        if given_first_type<given_second_type:
            given_second_type=type_inference_expr(expr.objects[2],[given_first_type],data_def)
        elif given_second_type<given_first_type:
            given_first_type=type_inference_expr(expr.objects[0],[given_second_type],data_def)
        # 按照更小的那个类型进行遍历，缩小范围
        if given_first_type!=given_second_type:
            raise TypeMismatchException(expr,required_given_type,data_def)
    expr.set_lhs_type([given_first_type])
    # 第一个子表达式，即左侧的那个表达式不管是什么操作符都是要返回的那个
    return expr.lhsTypeList

@inference_expr_handler('Relation_expr')
def type_inference_Relation(expr, lhs_type_list:list[SyntaxType],data_def):
    # =与<>不对子类型做限制
    # 其他情况，则限制为numeric
    # 两侧的类型必须一致
    # 返回类型肯定是bool，不用讨论
    if len(lhs_type_list) != 1 and lhs_type_list[0]!=SyntaxType('bool'):
        raise TypeMismatchException(expr, lhs_type_list, data_def)

    op=expr.objects[1]
    if op=="=" or op=="<>":
        required_type=SyntaxType("any")
    else:
        required_type=SyntaxType("numeric")
    given_first_type = type_inference_expr(expr.objects[0],[required_type],data_def)[0]
    given_second_type = type_inference_expr(expr.objects[2],[required_type],data_def)[0]
    if given_first_type < given_second_type:
        given_second_type = type_inference_expr(expr.objects[2], [given_first_type], data_def)
    elif given_second_type<given_first_type:
        given_first_type = type_inference_expr(expr.objects[0], [given_second_type], data_def)
    # 按照更小的那个类型进行遍历，缩小范围
    if given_first_type != given_second_type:
        raise TypeMismatchException(expr,given_second_type , data_def)
    
    expr.set_lhs_type([SyntaxType('bool')])
    return expr.lhsTypeList

@inference_expr_handler('List_expr')
def type_inference_List(expr, lhs_type_list:list[SyntaxType],data_def):
    #需要每个表达式在后处理哪里先记一下自己返回多少个变量，可恶
    #↑做好了，比想象的简单很多，大部分expr只接受1一个输出
    # 然后根据子表达式的返回变量情况，把输入的变量类型发送下去做校验
    expr_list=expr.objects[0]
    cur_index=0
    actual_type_list=list()
    for sub_expr in expr_list:
        expect_num=sub_expr.returnNum
        actual_type=type_inference_expr(sub_expr,lhs_type_list[cur_index:cur_index+expect_num],data_def)
        actual_type_list.extend(actual_type)
        cur_index+=expect_num
    expr.set_lhs_type(actual_type_list)
    return expr.lhsTypeList


inference_apply_handlers={}
def inference_apply_handler(type_):
    def decorator(func):
        inference_apply_handlers[type_] = func
        return func

    return decorator

@inference_expr_handler("Apply_expr")
def type_inference_Apply(expr, lhs_type_list:list[SyntaxType],data_def):
    #设置这个expr函数调用情况，即对调用函数封装的层次，用于outC中
    #以一个字典的形式保存，map( map func<<3>>)<<2>> 得到的字典是{func:[2,3]}
    operator=expr.objects[0]
    handler=inference_apply_handlers.get(operator.subtype)
    if handler is None:
        raise Exception(f"不对,{operator.subtype}还没实现")
    handler(operator,expr,lhs_type_list,data_def)

@inference_apply_handler("Path_id")
def type_inference_apply_path_id(operator:SyntaxOperator,expr:SyntaxExpr,lhs_type_list:list[SyntaxType],data_def):
    tar_userOp=operator.appliedUserOp
