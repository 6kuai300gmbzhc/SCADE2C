from syntax_tree.SyntaxClass import *
from syntax_tree.scade_preprocess import *

import automaton_generate as automaton_generate
class GenerateCode:
    def __init__(self,mainNode):
        self.mainNode = mainNode
class GenEqu:
    expr: str
    preEquations: list
    '''若需要使用到中间变量，中间变量的定义需要在该equation之前，是一个列表，列表里的元素是一个C语句'''
    postEquations: list
    '''fby生成的C代码需要在该equation之后'''

    def __init__(self):
        self.expr = ""
        self.preEquations=[]
        self.postEquations=[]

    def add_preEquations(self,equations):
        self.preEquations.append(equations)

    def add_postEquations(self,equations):
        self.postEquations.append(equations)

    def __str__(self):
        code = ""
        code += "".join(self.preEquations)
        code += "".join(self.postEquations)
        code += "\n ====\n"
        code += self.expr
        code += "\n ==== \n"
        return code

generate_switch_expr_handlers = {}
def register_switch_expr_handler(type_):
    def decorator(func):
        generate_switch_expr_handlers[type_]=func
        return func
    return decorator

@register_switch_expr_handler("IF")
def generate_switch_expr_if(syntax_switch_expr_objects,syntaxUserOp,genEqu):
    return f"({SyntaxExpr_generate(syntax_switch_expr_objects[0],syntaxUserOp,genEqu)} ? {SyntaxExpr_generate(syntax_switch_expr_objects[1],syntaxUserOp,genEqu)} : {SyntaxExpr_generate(syntax_switch_expr_objects[2],syntaxUserOp,genEqu)})"

@register_switch_expr_handler("CASE")
def generate_switch_expr_case(syntax_switch_expr_objects,syntaxUserOp,genEqu):
    return ""

generate_bool_expr_handlers = {}
def register_bool_expr_handler(type_):
    def decorator(func):
        generate_bool_expr_handlers[type_]=func
        return func
    return decorator

@register_bool_expr_handler("NOT")
def generate_bool_expr_not(syntax_bool_expr_objects,syntaxUserOp,genEqu):
    return f"( !({SyntaxExpr_generate(syntax_bool_expr_objects[0],syntaxUserOp,genEqu)}) )"

@register_bool_expr_handler("HASHTAG")
def generate_bool_expr_hashtag(syntax_bool_expr_objects,syntaxUserOp,genEqu):
    code = "(("
    for idx,obj in enumerate(syntax_bool_expr_objects[0]):
        if idx !=0 :
            code += "+"
        code += SyntaxExpr_generate(obj,syntaxUserOp,genEqu)
    code += ") <= 1)"
    return code

@register_bool_expr_handler("binOp")
def generate_bool_expr_binop(syntax_bool_expr_objects,syntaxUserOp,genEqu):
    binOp_dict = {"and":" & ","or":" | ","xor":" ^ "}
    return f"({SyntaxExpr_generate(syntax_bool_expr_objects[0],syntaxUserOp,genEqu)}{binOp_dict[syntax_bool_expr_objects[1]]}{SyntaxExpr_generate(syntax_bool_expr_objects[2],syntaxUserOp,genEqu)})"

generate_atom_expr_handlers = {}
def register_atom_expr_handler(type_):
    def decorator(func):
        generate_atom_expr_handlers[type_]=func
        return func
    return decorator

@register_atom_expr_handler("bool_atom")
def generate_atom_expr_bool(syntax_atom_expr_objects,syntaxUserOp,genEqu):
    return f"kcg_{syntax_atom_expr_objects[0]}"

@register_atom_expr_handler("integernum")
def generate_atom_expr_integernum(syntax_atom_expr_objects,syntaxUserOp,genEqu):
    return syntax_atom_expr_objects[0]

@register_atom_expr_handler("floatnum")
def generate_atom_expr_floatnum(syntax_atom_expr_objects,syntaxUserOp,genEqu):
    return syntax_atom_expr_objects[0]

@register_atom_expr_handler("character")
def generate_atom_expr_character(syntax_atom_expr_objects,syntaxUserOp,genEqu):
    return syntax_atom_expr_objects[0]

@register_atom_expr_handler("typed_integer")
def generate_atom_expr_typed_integer(syntax_atom_expr_objects,syntaxUserOp,genEqu):
    return ""

@register_atom_expr_handler("typed_float")
def generate_atom_expr_typed_float(syntax_atom_expr_objects,syntaxUserOp,genEqu):
    return ""

generate_relation_expr_handlers = {}

def register_relation_expr_handler(type_):
    def decorator(func):
        generate_relation_expr_handlers[type_]=func
        return func
    return decorator

@register_relation_expr_handler('Relation_expr')
def generate_relation_expr(syntax_relation_expr_objects,syntaxUserOp,genEqu):
    op = syntax_relation_expr_objects[1]
    if op == '<>':
        op = '!='
    elif op == '=':
        op = '=='
    return f"({SyntaxExpr_generate(syntax_relation_expr_objects[0],syntaxUserOp,genEqu)} {op} {SyntaxExpr_generate(syntax_relation_expr_objects[2],syntaxUserOp,genEqu)})"

generate_arith_expr_handlers = {}

def register_arith_expr_handler(type_):
    def decorator(func):
        generate_arith_expr_handlers[type_] = func
        return func
    return decorator

@register_arith_expr_handler('cast')
def generate_arith_expr_cast(syntax_arith_expr_objects,syntaxUserOp,genEqu):
    syntax_type = syntax_arith_expr_objects[1]
    expr = syntax_arith_expr_objects[0]
    return f"{(syntax_type.change_name())}({SyntaxExpr_generate(expr,syntaxUserOp,genEqu)})"

@register_arith_expr_handler('unary')
def generate_arith_expr_unary(syntax_arith_expr_objects,syntaxUserOp,genEqu):
    unary_op = syntax_arith_expr_objects[0]
    if unary_op == '+':
        return f"({SyntaxExpr_generate(syntax_arith_expr_objects[1],syntaxUserOp,genEqu)})"
    elif unary_op == '-':
        return f"{unary_op}({SyntaxExpr_generate(syntax_arith_expr_objects[1],syntaxUserOp,genEqu)})"
    else: #lnot需要在中间层转化为lnot_uXX,先用uint64替代，等Expr的exprType得到可以将其替换
        return f"kcg_lnot_uint64({SyntaxExpr_generate(syntax_arith_expr_objects[1],syntaxUserOp,genEqu)})"

@register_arith_expr_handler('binOp')
def generate_arith_expr_binOp(syntax_arith_expr_objects,syntaxUserOp,genEqu):
    #此处var_type需要等Expr的exprType设置完进行替换
    if syntax_arith_expr_objects[1]=='lsl':
        var_type = "uint64"
        return f"kcg_lsl_{var_type}({SyntaxExpr_generate(syntax_arith_expr_objects[0],syntaxUserOp,genEqu)},{SyntaxExpr_generate(syntax_arith_expr_objects[2],syntaxUserOp,genEqu)})"
    else:
        binop_dict = {"+":"+","-":"-","*":"*","/":"/","mod":"%","land":"&","lor":"|","lxor":"^","lsr":">>"}
        return f"{SyntaxExpr_generate(syntax_arith_expr_objects[0],syntaxUserOp,genEqu)} {binop_dict[syntax_arith_expr_objects[1]]} {SyntaxExpr_generate(syntax_arith_expr_objects[2],syntaxUserOp,genEqu)}"

generate_id_expr_handlers = {}

def register_id_expr_handler(type_):
    def decorator(func):
        generate_id_expr_handlers[type_] = func
        return func
    return decorator

@register_id_expr_handler("Path_id")
def generate_id_expr_path_id(syntax_id_expr_objects,syntaxUserOp,genEqu):
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
def generate_id_expr_single_quote_lv6id(syntax_id_expr_objects,syntaxUserOp,genEqu):
    return ""

@register_id_expr_handler("lastSinglequoteLv6id")
def generate_id_expr_last_single_quote_lv6id(syntax_id_expr_objects,syntaxUserOp,genEqu):
    return ""

@register_id_expr_handler("ID")
def generate_id_expr_ID(syntax_id_expr_objects,syntaxUserOp,genEqu):
    return ""

generate_expr_handlers = {}

def register_expr_handler(type_):
    def decorator(func):
        generate_expr_handlers[type_] = func
        return func
    return decorator

@register_expr_handler('Id_expr')
def generate_Id_expr(syntaxExpr,syntaxUserOp,genEqu):
    subtype_ = syntaxExpr.subType
    generate_id_expr_handler = generate_id_expr_handlers.get(subtype_)
    if generate_id_expr_handler:
        return generate_id_expr_handler(syntaxExpr.objects,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"generate_Id_expr , subtype:{subtype_}")

@register_expr_handler('Atom')
def generate_Atom_expr(syntaxExpr,syntaxUserOp,genEqu):
    subtype_ = syntaxExpr.subType
    generate_atom_expr_handler = generate_atom_expr_handlers.get(subtype_)
    if generate_atom_expr_handler:
        return generate_atom_expr_handler(syntaxExpr.objects,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"generate_Atom_expr , subtype:{subtype_}")

@register_expr_handler('Tempo_expr')
def generate_Tempo_expr(syntaxExpr,syntaxUserOp,genEqu):
    return ""

@register_expr_handler('Arith_expr')
def generate_Arith_expr(syntaxExpr,syntaxUserOp,genEqu):
    subtype_ =syntaxExpr.subType
    generate_arith_expr_handler = generate_arith_expr_handlers.get(subtype_)
    if generate_arith_expr_handler:
        return generate_arith_expr_handler(syntaxExpr.objects,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"generate_Arith_expr , subtype:{subtype_}")

@register_expr_handler('Relation_expr')
def generate_Relation_expr(syntaxExpr,syntaxUserOp,genEqu):
    subtype_ = syntaxExpr.subType
    generate_relation_expr_handler = generate_relation_expr_handlers.get(subtype_)
    if generate_relation_expr_handler:
        return generate_relation_expr_handler(syntaxExpr.objects,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"generate_Relation_expr , subtype:{subtype_}")

@register_expr_handler('List_expr')
def generate_List_expr(syntaxExpr,syntaxUserOp,genEqu):
    #长度只可能为1，lnot(in1),此处会使用list。list在中间层会被拆开。
    return SyntaxExpr_generate(syntaxExpr.objects[0][0],syntaxUserOp,genEqu)

@register_expr_handler('Switch_expr')
def generate_Switch_expr(syntaxExpr,syntaxUserOp,genEqu):
    subtype_ = syntaxExpr.subType
    generate_switch_expr_handler = generate_switch_expr_handlers.get(subtype_)
    if generate_switch_expr_handler:
        return generate_switch_expr_handler(syntaxExpr.objects,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"generate_Switch_expr , subtype:{subtype_}")

@register_expr_handler('Bool_expr')
def generate_Bool_expr(syntaxExpr,syntaxUserOp,genEqu):
    subtype_ = syntaxExpr.subType
    generate_bool_expr_handler = generate_bool_expr_handlers.get(subtype_)
    if generate_bool_expr_handler:
        return generate_bool_expr_handler(syntaxExpr.objects,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"generate_Bool_expr , subtype:{subtype_}")

@register_expr_handler('Struct_expr')
def generate_Struct_expr(syntaxExpr,syntaxUserOp,genEqu):
    return ""

@register_expr_handler('Array_expr')
def generate_Array_expr(syntaxExpr,syntaxUserOp,genEqu):
    return ""

@register_expr_handler('Apply_expr')
def generate_Apply_expr(syntaxExpr,syntaxUserOp,genEqu):
    return ""

@register_expr_handler('Mixed_constructor')
def generate_Mixed_constructor(syntaxExpr,syntaxUserOp,genEqu):
    return ""

def SyntaxExpr_generate(syntaxExpr,syntaxUserOp,genEqu):
    type_ = syntaxExpr.type
    generate_expr_handler = generate_expr_handlers.get(type_)
    if generate_expr_handler:
        return generate_expr_handler(syntaxExpr,syntaxUserOp,genEqu)
    else:
        raise ValueError(f"Unknown type: {type_}")


generate_userOp_handlers={}
def register_userOp_handler(type_):
    def decorator(func):
        generate_userOp_handlers[type_]=func
        return func
    return decorator

@register_userOp_handler("simple_equation")
def generate_userOp_simple_equation(syntaxEquation,syntaxUserOp):
    #out1=in1;若out1是数组或结构体，则需要使用memcpy，不能使用=。若右边是函数调用，且返回多个值，也不能直接使用=
    genEqu = GenEqu()
    genEqu.expr = SyntaxExpr_generate(syntaxEquation.expr,syntaxUserOp,genEqu)
    code = ""
    code += "".join(genEqu.preEquations)
    code += f"{syntaxUserOp.var_change_name(syntaxEquation.lhs[0])} = {genEqu.expr};\n"
    code += "".join(genEqu.postEquations)
    return code

@register_userOp_handler("assume")
def generate_userOp_assume(syntaxEquation,syntaxUserOp):
    return ""

@register_userOp_handler("guarantee")
def generate_userOp_guarantee(syntaxEquation,syntaxUserOp):
    return ""

@register_userOp_handler("emission")
def generate_userOp_emission(syntaxEquation,syntaxUserOp):
    return ""

@register_userOp_handler("control_block")
def generate_userOp_control_block(syntaxEquation:SyntaxEquation,syntaxUserOp:SyntaxUserOp):
    control_block_ID=syntaxEquation.controlBlockID
    control_block=syntaxUserOp.get_childScope(control_block_ID)
    if control_block is None:raise UnknownIdentifierException(f"control_block {control_block_ID} 没有找到")

    if control_block.type=="automaton":
        print("BODY:")
        print(automaton_generate.generate_body(control_block))
        print("TYPE:")
        print(automaton_generate.generate_type(control_block))
        print("HEAD:")
        print(automaton_generate.generate_head(control_block))
        print("INIT:")
        print(automaton_generate.generate_init(control_block))
        for name, state in control_block.childScopeTable.items():
            for name, scope in state.childScopeTable.items():
                if scope.type == "automaton":
                    print("BODY:")
                    print(automaton_generate.generate_body(scope))
                    print("TYPE:")
                    print(automaton_generate.generate_type(scope))
                    print("HEAD:")
                    print(automaton_generate.generate_head(scope))
                    print("INIT:")
                    print(automaton_generate.generate_init(scope))
        return ""
    else: return ""

def SyntaxUserOp_generate(syntaxUserOp):
    code = ""
    for elem in syntaxUserOp.equations:
        type_ = elem.type
        generate_userOp_handler = generate_userOp_handlers.get(type_)
        if generate_userOp_handler:
            code += generate_userOp_handler(elem,syntaxUserOp)
        else:
            raise ValueError(f"syntaxUserOp_generate error , type : {type_}")
    print("=== UserOp ===\n")
    print(code)
    print("==========")

def write_file_from_src_to_target(src,target):
    with open(src,'r') as src_file:
        content=src_file.read()
    with open(target,'w') as target_file:
        target_file.write(content)

def write_file(file_path,content,mode):
    with open(file_path,mode) as target_file:
        target_file.write(content)

def generate_const_equation(rootPackage):
    h_content = ""
    c_content = ""
    for _,packageScope in rootPackage.childScopeTable.items():
        h,c = generate_const_equation(packageScope)
        h_content += h
        c_content += c
    global_name = "_".join(rootPackage.get_global_name().split("::"))
    for name,constSymbol in rootPackage.constSymbolTable.items():
        symbol_name = name if len(global_name)==0 else f"{name}_{global_name}"
        symbol_type = constSymbol.syntaxType.change_name()
        if constSymbol.isImported ==True:
            h_content += f'''
            #ifndef {symbol_name}\n
            #define {symbol_name} {symbol_name}\n
            extern const {symbol_type} {symbol_name};\n
            #endif\n
           '''
        else:
            h_content += f"extern const {symbol_type} {symbol_name};\n"
            c_content += f"const {symbol_type} {symbol_name}={SyntaxExpr_generate(constSymbol.valueExpr,rootPackage,symbol_type)};\n"
    return h_content,c_content

class GenerateCode:
    def __init__(self,rootNode,mainNode,outputDir):
        self.rootNode=rootNode
        self.mainNode = mainNode
        # if not os.path.isdir(self.outputDir):
        #     os.makedirs(self.outputDir)
        mainNode = self.mainNode.split("::")
        self.outputDir = f"{outputDir}/{mainNode[-1]}" if len(mainNode) == 1 else f"{outputDir}/{mainNode[-1]}_{'_'.join(mainNode[:-1])}"
        # os.makedirs(f"{self.outputDir}/src")
        # os.makedirs(f"{self.outputDir}/include")

    def generate_const_file(self):
        #只要写了const_block无论是否使用都会使用,从root_node开始深度遍历
        c_content = '''
        #include "kcg_consts.h"
        '''
        h_content = ''''
        #ifndef _KCG_CONSTS_H_\n  
        #define _KCG_CONSTS_H_\n
        #include "kcg_types.h"\n
        '''

        h,c = generate_const_equation(self.rootNode)
        h_content += h
        c_content += c

        h_content += '''#endif'''
        # print("==== h_content ====\n",h_content)
        # print("==== c_content ====\n",c_content)
        # write_file(f"{self.outputDir}/include/kcg_consts.h",h_content,"w")
        # write_file(f"{self.outputDir}/src/kcg_consts.c",c_content,"w")


    def generate_sensor_file(self):
        pass

    def generate_types_file(self):
        src_file = "../template/kcg_types.h"
        target_file = f"{self.outputDir}/include/kcg_types.h"
        # write_file_from_src_to_target(src_file,target_file)

        #中间还需要写和types相关的内容

        content = "#endif"
        # write_file(target_file,content,"a")

    def generate_assign_file(self):
        src_file = "../template/kcg_assign.h"
        target_file = f"{self.outputDir}/include/kcg_assign.h"
        # write_file_from_src_to_target(src_file,target_file)

    def generate_imported_types_file(self):
        pass

    def generate_macro_libmathext_file(self):
        path_dict={"../template/macro_libmathext32.h":f"{self.outputDir}/include/macro_libmathext32.h","../template/macro_libmathext64.h":f"{self.outputDir}/include/macro_libmathext64.h"}
        for k,v in path_dict.items():
            write_file_from_src_to_target(k,v)

    def generate_main_file(self):
        pass

def scade_generate(root_operator):
    for k,v in root_scope.userOpTable.items():
        SyntaxUserOp_generate(v)

def scade_parse(input_path:str,main_operator:str,output_path:str):
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

    gen = GenerateCode(root_scope,main_operator,output_path)
    # gen.generate_const_file()
    # gen.generate_main_file()

    scade_generate(main_operator)


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-m', '--main_operator', required=True, type=str)
    argParser.add_argument('-o','--output_path',required=True,type=str)
    args = argParser.parse_args()
    scade_parse(args.input_path, args.main_operator,args.output_path)