from syntax_tree.SyntaxClass import *
from syntax_tree.scade_preprocess import *

class GenerateCode:
    def __init__(self,mainNode):
        self.mainNode = mainNode

generate_atom_expr_handlers = {}
def register_atom_expr_handler(type_):
    def decorator(func):
        generate_atom_expr_handlers[type_]=func
        return func
    return decorator

@register_atom_expr_handler("bool_atom")
def generate_atom_expr_bool(syntax_atom_expr_objects,syntaxUserOp,lhs):
    return f"kcg_{syntax_atom_expr_objects[0]}"

@register_atom_expr_handler("integernum")
def generate_atom_expr_integernum(syntax_atom_expr_objects,syntaxUserOp,lhs):
    return syntax_atom_expr_objects[0]

@register_atom_expr_handler("floatnum")
def generate_atom_expr_floatnum(syntax_atom_expr_objects,syntaxUserOp,lhs):
    return syntax_atom_expr_objects[0]

@register_atom_expr_handler("character")
def generate_atom_expr_character(syntax_atom_expr_objects,syntaxUserOp,lhs):
    return syntax_atom_expr_objects[0]

@register_atom_expr_handler("typed_integer")
def generate_atom_expr_typed_integer(syntax_atom_expr_objects,syntaxUserOp,lhs):
    return ""

@register_atom_expr_handler("typed_float")
def generate_atom_expr_typed_float(syntax_atom_expr_objects,syntaxUserOp,lhs):
    return ""


generate_relation_expr_handlers = {}

def register_relation_expr_handler(type_):
    def decorator(func):
        generate_relation_expr_handlers[type_]=func
        return func
    return decorator

@register_relation_expr_handler('Relation_expr')
def generate_relation_expr(syntax_relation_expr_objects,syntaxUserOp,lhs):
    op = syntax_relation_expr_objects[1]
    if op == '<>':
        op = '!='
    elif op == '=':
        op = '=='
    return SyntaxExpr_generate(syntax_relation_expr_objects[0],syntaxUserOp,lhs) + op + SyntaxExpr_generate(syntax_relation_expr_objects[2],syntaxUserOp,lhs)

generate_arith_expr_handlers = {}

def register_arith_expr_handler(type_):
    def decorator(func):
        generate_arith_expr_handlers[type_] = func
        return func
    return decorator

@register_arith_expr_handler('cast')
def generate_arith_expr_cast(syntax_arith_expr_objects,syntaxUserOp,lhs):
    syntax_type = syntax_arith_expr_objects[1]
    expr = syntax_arith_expr_objects[0]
    return f"{(syntax_type.change_name())}({SyntaxExpr_generate(expr,syntaxUserOp,lhs)})"

@register_arith_expr_handler('unary')
def generate_arith_expr_unary(syntax_arith_expr_objects,syntaxUserOp,lhs):
    unary_op = syntax_arith_expr_objects[0]
    var_type = syntaxUserOp.get_localVariable(lhs[0]).syntaxType.type
    if unary_op == '+':
        return f"({SyntaxExpr_generate(syntax_arith_expr_objects[1],syntaxUserOp,lhs)})"
    elif unary_op == '-':
        return f"{unary_op}({SyntaxExpr_generate(syntax_arith_expr_objects[1],syntaxUserOp,lhs)})"
    elif unary_op == 'lnot':
        return f"kcg_lnot_{var_type}({SyntaxExpr_generate(syntax_arith_expr_objects[1],syntaxUserOp,lhs)})"

@register_arith_expr_handler('binOp')
def generate_arith_expr_binOp(syntax_arith_expr_objects,syntaxUserOp,lhs):
    var_type = syntaxUserOp.get_localVariable(lhs[0]).syntaxType.type
    if syntax_arith_expr_objects[1]=='lsl':
        return f"kcg_lsl_{var_type}({SyntaxExpr_generate(syntax_arith_expr_objects[0],syntaxUserOp,lhs)},{SyntaxExpr_generate(syntax_arith_expr_objects[2],syntaxUserOp,lhs)})"
    else:
        binop_dict = {"+":" + ","-":" - ","*":" * ","/":" / ","mod":" % ","land":" & ","lor":" | ","lxor":" ^ ","lsr":" >> "}
        return SyntaxExpr_generate(syntax_arith_expr_objects[0],syntaxUserOp,lhs) + binop_dict[syntax_arith_expr_objects[1]] + SyntaxExpr_generate(syntax_arith_expr_objects[2],syntaxUserOp,lhs)

generate_id_expr_handlers = {}

def register_id_expr_handler(type_):
    def decorator(func):
        generate_id_expr_handlers[type_] = func
        return func
    return decorator

@register_id_expr_handler("Path_id")
def generate_id_expr_path_id(syntax_id_expr_objects,syntaxUserOp,lhs):
    #TODO:如果path_id是包含“::”的路径名，生成代码时需要将::替换为_，需要修改路径的顺序
    # symbol = syntaxUserOp.get_localVariable(syntax_id_expr_objects[0])
    # if symbol != None:
    #     if symbol.isOutput:
    #         return f"outC->{symbol.name}"
    #     elif symbol.isInput:
    #         return f"inC->{symbol.name}"
    #     else:
    #         return symbol.name
    # else:
    #     raise ValueError(f"generate_id_expr_path_id error, path_id:{syntax_id_expr_objects[0]}")
    return syntaxUserOp.var_change_name(syntax_id_expr_objects[0])
        

@register_id_expr_handler("singlequoteLv6id")
def generate_id_expr_single_quote_lv6id(syntax_id_expr_objects,syntaxUserOp,lhs):
    return ""

@register_id_expr_handler("lastSinglequoteLv6id")
def generate_id_expr_last_single_quote_lv6id(syntax_id_expr_objects,syntaxUserOp,lhs):
    return ""

@register_id_expr_handler("ID")
def generate_id_expr_ID(syntax_id_expr_objects,syntaxUserOp,lhs):
    return ""

generate_expr_handlers = {}

def register_expr_handler(type_):
    def decorator(func):
        generate_expr_handlers[type_] = func
        return func
    return decorator

@register_expr_handler('Id_expr')
def generate_Id_expr(syntaxExpr,syntaxUserOp,lhs):
    subtype_ = syntaxExpr.subType
    generate_id_expr_handler = generate_id_expr_handlers.get(subtype_)
    if generate_id_expr_handler:
        return generate_id_expr_handler(syntaxExpr.objects,syntaxUserOp,lhs)
    else:
        raise ValueError(f"generate_Id_expr , subtype:{subtype_}")

@register_expr_handler('Atom')
def generate_Atom_expr(syntaxExpr,syntaxUserOp,lhs):
    subtype_ = syntaxExpr.subType
    generate_atom_expr_handler = generate_atom_expr_handlers.get(subtype_)
    if generate_atom_expr_handler:
        return generate_atom_expr_handler(syntaxExpr.objects,syntaxUserOp,lhs)
    else:
        raise ValueError(f"generate_Atom_expr , subtype:{subtype_}")

@register_expr_handler('Tempo_expr')
def generate_Tempo_expr(syntaxExpr,syntaxUserOp,lhs):
    return ""

@register_expr_handler('Arith_expr')
def generate_Arith_expr(syntaxExpr,syntaxUserOp,lhs):
    subtype_ =syntaxExpr.subType
    generate_arith_expr_handler = generate_arith_expr_handlers.get(subtype_)
    if generate_arith_expr_handler:
        return generate_arith_expr_handler(syntaxExpr.objects,syntaxUserOp,lhs)
    else:
        raise ValueError(f"generate_Arith_expr , subtype:{subtype_}")

@register_expr_handler('Relation_expr')
def generate_Relation_expr(syntaxExpr,syntaxUserOp,lhs):
    subtype_ = syntaxExpr.subType
    generate_relation_expr_handler = generate_relation_expr_handlers.get(subtype_)
    if generate_relation_expr_handler:
        return generate_relation_expr_handler(syntaxExpr.objects,syntaxUserOp,lhs)
    else:
        raise ValueError(f"generate_Relation_expr , subtype:{subtype_}")

@register_expr_handler('List_expr')
def generate_List_expr(syntaxExpr,syntaxUserOp,lhs):
    #长度只可能为1，lnot(in1),此处会使用list。list在中间层会被拆开。
    return SyntaxExpr_generate(syntaxExpr.objects[0][0],syntaxUserOp,lhs)

@register_expr_handler('Switch_expr')
def generate_Switch_expr(syntaxExpr,syntaxUserOp,lhs):
    return ""

@register_expr_handler('Bool_expr')
def generate_Bool_expr(syntaxExpr,syntaxUserOp,lhs):
    return ""

@register_expr_handler('Struct_expr')
def generate_Struct_expr(syntaxExpr,syntaxUserOp,lhs):
    return ""

@register_expr_handler('Array_expr')
def generate_Array_expr(syntaxExpr,syntaxUserOp,lhs):
    return ""

@register_expr_handler('Apply_expr')
def generate_Apply_expr(syntaxExpr,syntaxUserOp,lhs):
    return ""

@register_expr_handler('Mixed_constructor')
def generate_Mixed_constructor(syntaxExpr,syntaxUserOp,lhs):
    return ""

def SyntaxExpr_generate(syntaxExpr,syntaxUserOp,lhs):
    type_ = syntaxExpr.type
    generate_expr_handler = generate_expr_handlers.get(type_)
    if generate_expr_handler:
        return generate_expr_handler(syntaxExpr,syntaxUserOp,lhs)
    else:
        raise ValueError(f"Unknown type: {type_}")
    
def SyntaxUserOp_generate(syntaxUserOp):
    #首先遍历其equations，还需要遍历其子作用域
    # print("SyntaxUserOp_generate",syntaxUserOp.lhs,syntaxUserOp.expr)
    userOp_code = ""
    for elem in syntaxUserOp.equations:
        if elem.type == "simple_equation":
            if elem.expr.type != 'Apply_expr':
                userOp_code += f"{syntaxUserOp.var_change_name(elem.lhs[0])} = {SyntaxExpr_generate(elem.expr,syntaxUserOp,elem.lhs)};\n"
        elif elem.type == "assume":
            pass
        elif elem.type == "guarantee":
            pass
        elif elem.type == "emission":
            pass
        elif elem.type == "control_block":
            pass 
    print("SyntaxUserOp_generate\n",userOp_code)

def scade_generate(root_operator):
    for k,v in root_scope.userOpTable.items():
        SyntaxUserOp_generate(v)

def scade_parse(input_path:str,root_operator:str):
    parser = yacc(debug=1, start="Program")

    file = open(input_path, 'r')
    strs = file.read()

    pattern1 = r'#pragma [a-zA-Z0-9_!"$#%&\'()*+,\-./:;_<=>?@\\^`|{}~\s]*?#end'
    strs = re.sub(pattern1, '', strs, flags=re.MULTILINE)

    pattern2 = r'\#[\w]+'
    strs = re.sub(pattern2, '', strs)

    pattern3 = re.compile(r'/\*.*?\*/', re.DOTALL)
    strs = re.sub(pattern3, '', strs)

    print("=======strs=====\n", strs)
    string_tokens = get_tokens(strs)
    scade_lexer.set_tokens(string_tokens)
    nodes = parser.parse(strs, lexer=scade_lexer)

    root_node_deque=deque()
    root_node_deque.extend(root_operator.split("::"))
    scade_generate(root_node_deque)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-r', '--root_operator', required=True, type=str)
    args = argParser.parse_args()
    scade_parse(args.input_path, args.root_operator)