from syntax_tree.SyntaxClass import *



const_expr_handlers = {}


def const_expr_handler(type_):
    def decorator(func):
        const_expr_handlers[type_] = func
        return func

    return decorator


def cal_const_expr(expr: SyntaxExpr) -> ConstValue:
    """计算常数表达式，得到具体值
    允许的表达式类型：
    userOP对应的size_decl,非imported的const值->Path_id
    Arith_expr中的unary,binOp->unary,binOp
    atom中的integernum->integernum
    常数数组与结构体的取数操作->接受construct和list两个类型，就是可以现场构造一个常数表达式，还有get->get,construct,list
    不能用make现场搓结构体
    List_expr也可以，当括号使用
    两个get，两个construct都可以使用
    常值计算：
    Relation_expr
    Bool_expr的NOT和binOp
    并且还有枚举类型的具体赋值情况，这个先不考虑
    考虑到要兼容常数类型的赋值问题，不能仅局限于整形变量的计算
    还需要引入类型校验，来进行匹配
    不需要进行拓扑排序
    对于size_decl等需要返回int值
    对常量赋值需要返回兼容常量的值
    """
    _type = expr.type
    handler = const_expr_handlers.get(_type)
    if handler is None:
        raise NotStaticExprException(expr)
    return handler(expr)


@const_expr_handler("Id_expr")
def const_path_id(expr: SyntaxExpr) -> ConstValue:
    if expr.subType == "ID":
        return ConstValue(syntax_type=SyntaxType("ID"), value=expr.objects[0])

    if expr.subType != "Path_id":
        raise NotStaticExprException(expr)
    path_id = expr.objects[0]
    scope = expr.scope
    const_symbol = scope.check_and_get_constant_param(path_id)
    if not const_symbol or const_symbol.isImported:
        raise UnknownIdentifierException(path_id)
    return ConstValue(syntax_type=const_symbol.syntaxType, value=const_symbol.get_value())


@const_expr_handler("Atom")
def const_integernum(expr: SyntaxExpr) -> ConstValue:
    given_type, value = get_type_and_value_for_atom(expr)
    return ConstValue(syntax_type=SyntaxType(given_type), value=value)

# @const_expr_handler("Arith_expr")
# def const_unary(expr: SyntaxExpr) -> int:
#     unary_op = expr.objects[0]
#     value = cal_const_expr(expr.objects[1])
#     if type(value) != int:
#         raise TypeMismatchException(value, "int")
#     if unary_op == "-":
#         return -value
#     else:
#         return value
#
#
# @const_expr_handler("Arith_expr")
# def const_binOp(expr: SyntaxExpr) -> int:
#     # + and -, *, /, mod, land, lor, lxor, lsl,lsr
#     binOP = expr.objects[1]
#     value_left = cal_const_expr(expr.objects[0])
#     if type(value_left) != int:
#         raise TypeMismatchException(value_left, "int")
#     value_right = cal_const_expr(expr.objects[2])
#     if type(value_right) != int:
#         raise TypeMismatchException(value_right, "int")
#     return eval(f"{str(value_left)}{SyntaxExpr.binop_dict[binOP]}{str(value_right)}")
