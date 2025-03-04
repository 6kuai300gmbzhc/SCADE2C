import SymbolClass
from syntax_tree.SyntaxClass import *
from syntax_tree.scade_preprocess import *
from syntax_tree.scade_postprocess import post_process
from functools import wraps

# 暂时使用，当把每个expr的type都设置了，就可以不使用了
lhs_type = ""

import syntax_tree.automaton_generate as automaton_generate


class GenerateCode:
    def __init__(self, rootNode, mainNode, outputDir):
        self.rootNode = rootNode
        self.mainNode = mainNode
        self.outputDir = outputDir
        if not os.path.isdir(self.outputDir):
            os.makedirs(self.outputDir)
        mainNode = self.mainNode.split("::")
        self.outputDir = f"{outputDir}/{mainNode[-1]}" if len(
            mainNode) == 1 else f"{outputDir}/{mainNode[-1]}_{'_'.join(mainNode[:-1])}"
        if not os.path.exists(f"{self.outputDir}/src"): os.makedirs(f"{self.outputDir}/src")
        if not os.path.exists(f"{self.outputDir}/include"): os.makedirs(f"{self.outputDir}/include")

    def generate_const_file(self):
        # 只要写了const_block无论是否使用都会使用,从root_node开始深度遍历
        c_content = '''#include "kcg_consts.h"\n'''
        h_content = '''#ifndef _KCG_CONSTS_H_\n#define _KCG_CONSTS_H_\n#include "kcg_types.h"\n'''

        h, c = generate_const_equation(self.rootNode)
        h_content += h
        c_content += c

        h_content += '''#endif'''
        # print("==== h_content ====\n",h_content)
        # print("==== c_content ====\n",c_content)
        # write_file(f"{self.outputDir}/include/kcg_consts.h",h_content,"w")
        # write_file(f"{self.outputDir}/src/kcg_consts.c",c_content,"w")
        with open("%s/include/kcg_consts.h" % (self.outputDir), 'w') as f:
            f.write(h_content)
        with open("%s/src/kcg_consts.c" % (self.outputDir), 'w') as f:
            f.write(c_content)

    def generate_sensor_file(self):
        pass

    def generate_types_file(self):
        src_file = "./template/kcg_types.h"
        target_file = f"{self.outputDir}/include/kcg_types.h"
        # write_file_from_src_to_target(src_file,target_file)

        # 中间还需要写和types相关的内容

        content = "#endif"
        with open(target_file, 'w') as target:
            with open(src_file, 'r') as src:
                target.write(src.read())
            target.write(generate_type_block(self.rootNode))

    def add_code_to_types_file(self, code: str):
        target_file = f"{self.outputDir}/include/kcg_types.h"
        with open(target_file, "a") as target:
            target.write(code)

    # write_file(target_file,content,"a")

    def generate_assign_file(self):
        src_file = "../template/kcg_assign.h"
        target_file = f"{self.outputDir}/include/kcg_assign.h"
        # write_file_from_src_to_target(src_file,target_file)

    def generate_imported_types_file(self):
        pass

    def generate_macro_libmathext_file(self):
        path_dict = {"../template/macro_libmathext32.h": f"{self.outputDir}/include/macro_libmathext32.h",
                     "../template/macro_libmathext64.h": f"{self.outputDir}/include/macro_libmathext64.h"}
        for k, v in path_dict.items():
            write_file_from_src_to_target(k, v)

    def generate_head_inC(self, node):
        global_name = node.get_global_name()
        code = "typedef struct{\n"
        for para in node.inParams:
            code += f"    {para.syntaxType.change_name()} {para.name};\n"
        code += f"}}inC_{global_name};\n"
        return code

    def generate_head_outC(self, node):
        global_name = node.get_global_name()
        code = "typedef struct{\n"
        # 这里要将node及其以下的所有子作用域的out情况都统计进来
        # 所以写一个深度优先搜索吧
        stack = deque()
        stack.append(node)
        # 只有最上层的状态机需要登记outC，其他不需要
        # 只有userOP有outParams，也就是最上层节点
        for para in node.outParams:
            code += f"    {para.syntaxType.change_name()} {para.name};\n"
        for name, child_scope in node.childScopeTable.items():
            if child_scope.type == "automaton":
                code += automaton_generate.generate_init_symbol_for_head(child_scope)
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)
            if cur_node.type == "automaton":
                code += automaton_generate.generate_state_nxt_for_head(cur_node)

            for para in cur_node.tmpParams:
                if para.isOutput:
                    print("para out", para.name)
                    code += f"    {para.syntaxType.change_name()} {para.name};\n"

        code += f"}}outC_{global_name};\n"
        return code

    def generate_head_func(self, node):
        global_name = node.get_global_name()
        code = f'''extern void {global_name}(inC_{global_name} *inC,outC_{global_name} *outC);\n'''
        return code

    def generate_head_other_func(self, node):
        global_name = node.get_global_name()
        code = f"extern void {global_name}_reset(outC_{global_name} *outC);\n" \
               f"extern void {global_name}_init(outC_{global_name} *outC);\n"
        return code

    def generate_head_file(self, node):
        global_name = node.get_global_name()
        head_content = f'#ifndef _{global_name}_H_\n#define _{global_name}_H_\n#include"kcg_types.h"\n'
        head_content += self.generate_head_inC(node)
        head_content += self.generate_head_outC(node)
        head_content += self.generate_head_func(node)
        head_content += self.generate_head_other_func(node)

        head_content += f"#endif"
        # print("==== head_content ====\n")
        # print(head_content)
        # print("=======================\n")
        target_file = f"{self.outputDir}/include/{global_name}.h"
        with open(target_file, "w") as target:
            target.write(head_content)

    def generate_src_func_file(self, node, body_content):
        global_name = node.get_global_name()
        post_content = ""
        src_content = ""
        src_content += f"void {global_name}(inC_{global_name} *inC,outC_{global_name} *outC){{\n"
        # localVariable + tmpVariable
        for name, symbol in node.localSymbolTable.items():
            src_content += f"{symbol.syntaxType.change_name()} {name};\n"
        for signal in node.signalSymbolSet:
            src_content += f"kcg_bool {signal};\n"
        for paraSymbol in node.tmpParams:
            if paraSymbol.isOutput == False:
                src_content += f"{paraSymbol.syntaxType.change_name()} {paraSymbol.name};\n"
            if paraSymbol.postExpr != None:
                genEqu = GenEqu()
                post_content += "".join(genEqu.preEquations)
                post_content += f"{node.var_change_name(paraSymbol.name)} = {SyntaxExpr_generate(paraSymbol.postExpr, node, genEqu)};\n"
                post_content += "".join(genEqu.postEquations)
        # body
        src_content += body_content
        # init,pre等的后处理语句
        src_content += post_content
        src_content += f"}}\n"
        print("==== src_content ====\n")
        print(src_content)
        print("======================")
        return src_content

    def generate_src_init(self, node):

        global_name = node.get_global_name()
        code = "#ifndef KCG_USER_DEFINED_INIT\n" \
               f"void {global_name}_init(outC_{global_name} *outC)\n" \
               "{\n"
        # 与outC部分是同理的，需要统计全部作用域中的变量，所以用深度优先遍历一下
        # 给每个outC里面的变量赋值，不包括状态机的部分
        stack = deque()
        stack.append(node)
        # 只有最上层的状态机需要登记outC，其他不需要
        # 只有userOP有outParams，也就是最上层节点
        for para in node.outParams:
            code += f"    outC->{para.name} = {para.syntaxType.generate_init_expr()};\n"
        # 给状态机设置初始状态
        for name, child_scope in node.childScopeTable.items():
            if child_scope.type == "automaton":
                code += automaton_generate.generate_init_symbol_for_init(child_scope)
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)
            if cur_node.type == "automaton":
                code += automaton_generate.generate_state_nxt_for_init(cur_node)

            for para in cur_node.tmpParams:
                if para.isOutput:
                    print("para init ", para.name)
                    code += f"    outC->{para.name} = {para.syntaxType.generate_init_expr()};\n"

        code += "}\n" \
                "#endif\n"
        return code

    def generate_src_reset(self, node):
        return ""

    def generate_src_file(self, node, body_content):
        global_name = node.get_global_name()
        src_content = f'''#include "kcg_consts.h"\n#include "{global_name}.h"\n'''
        src_content += self.generate_src_func_file(node, body_content)
        src_content += self.generate_src_init(node)
        src_content += self.generate_src_reset(node)

        target_file = f"{self.outputDir}/src/{global_name}.c"
        with open(target_file, "w") as target:
            target.write(src_content)

    def generate_node_file(self, node):
        body_content = SyntaxUserOp_generate(node, self)
        self.generate_src_file(node, body_content)
        self.generate_head_file(node)


class GenEqu:
    expr: str
    preEquations: list
    '''若需要使用到中间变量，中间变量的定义需要在该equation之前，是一个列表，列表里的元素是一个C语句'''
    postEquations: list
    '''fby生成的C代码需要在该equation之后'''

    depth: int
    '''这个语句所需要的缩进，默认是0'''

    def __init__(self, depth=0):
        self.expr = ""
        self.preEquations = []
        self.postEquations = []
        self.depth = depth

    def add_preEquations(self, equations):
        self.preEquations.append(equations)

    def add_postEquations(self, equations):
        self.postEquations.append(equations)

    def __str__(self):
        code = ""
        code += "".join(self.preEquations)
        code += "".join(self.postEquations)
        code += "\n ====\n"
        code += self.expr
        code += "\n ==== \n"
        return code


generate_tempo_expr_handlers = {}


def register_tempo_expr_hander(type_):
    def decorator(func):
        generate_tempo_expr_handlers[type_] = func
        return func

    return decorator


@register_tempo_expr_hander("ARROW")
def generate_tempo_expr_arrow(syntax_tempo_expr_objects, syntaxUserOp, genEqu):
    init_var = syntaxUserOp.set_init_var()
    code_ = f"({syntaxUserOp.var_change_name(init_var.name)} ? ({SyntaxExpr_generate(syntax_tempo_expr_objects[0], syntaxUserOp, genEqu)}) : ({SyntaxExpr_generate(syntax_tempo_expr_objects[1], syntaxUserOp, genEqu)}))"
    print("arrow set_init_var", len(syntaxUserOp.tmpParams), syntaxUserOp.name)
    # print("arrow set_init_var",syntaxUserOp.tmpParams)
    for elem in syntaxUserOp.tmpParams:
        print("===", elem.name)
    return code_


@register_tempo_expr_hander("PRE")
def generate_tempo_expr_pre(syntax_tempo_expr_objects, syntaxUserOp, genEqu):
    tmp_var_name = syntaxUserOp.generate_name_for_tmp()
    tmp_var = SyntaxVariableSymbol(tmp_var_name, False, False)
    tmp_var.syntaxType = SyntaxType(lhs_type)
    tmp_var.isOutput = True
    tmp_var.postExpr = syntax_tempo_expr_objects[0]
    syntaxUserOp.add_tmpSymbol(tmp_var)
    return syntaxUserOp.var_change_name(tmp_var_name)


@register_tempo_expr_hander("FBY")
def generate_tempo_expr_fby(syntax_tempo_expr_objects, syntaxUserOp, genEqu):
    tmp_idx_var = syntaxUserOp.generate_name_for_tmp()
    tmp_arr_var = syntaxUserOp.generate_name_for_tmp()
    tmp_var = syntaxUserOp.generate_name_for_tmp()
    idxVar = SyntaxVariableSymbol(tmp_idx_var, False, False)
    idxVar.isOutput = True
    idxVar.syntaxType = SyntaxType("path_id")
    idxVar.syntaxType.value = "kcg_size"

    arrVar = SyntaxVariableSymbol(tmp_arr_var, False, False)
    arrVar.isOutput = True
    arrSyntaxType = SyntaxType("list")
    arrSyntaxType.listExpr = syntax_tempo_expr_objects[1]
    arrSyntaxType.listType = SyntaxType(lhs_type)
    arrVar.syntaxType = arrSyntaxType

    tmpVar = SyntaxVariableSymbol(tmp_var, False, False)
    tmpVar.syntaxType = SyntaxType(lhs_type)

    initVar = syntaxUserOp.set_init_var()
    preCode = f'''
    if(outC->{syntaxUserOp.var_change_name(initVar.name)}){{\n
    for(int idx=0;idx<{SyntaxExpr_generate(syntax_tempo_expr_objects[1], syntaxUserOp, genEqu)};idx++){{\n
        {syntaxUserOp.var_change_name(tmp_arr_var)}[idx] = {SyntaxExpr_generate(syntax_tempo_expr_objects[2], syntaxUserOp, genEqu)};\n
        }}\n
        {syntaxUserOp.var_change_name(tmp_idx_var)} = 0;\n
    }}\n
    {tmp_var} = {syntaxUserOp.var_change_name(tmp_arr_var)}[{syntaxUserOp.var_change_name(tmp_idx_var)}];\n    
'''
    postCode = f'''
    {syntaxUserOp.var_change_name(tmp_arr_var)}[{syntaxUserOp.var_change_name(tmp_idx_var)}]={SyntaxExpr_generate(syntax_tempo_expr_objects[0], syntaxUserOp, genEqu)};\n
    {syntaxUserOp.var_change_name(tmp_idx_var)}=({syntaxUserOp.var_change_name(tmp_idx_var)}+1)%({SyntaxExpr_generate(syntax_tempo_expr_objects[1], syntaxUserOp, genEqu)});\n
    '''
    syntaxUserOp.add_tmpSymbol(idxVar)
    syntaxUserOp.add_tmpSymbol(arrVar)
    syntaxUserOp.add_tmpSymbol(tmpVar)

    genEqu.add_preEquations(preCode)
    genEqu.add_postEquations(postCode)
    return tmp_var


@register_tempo_expr_hander("TIMES")
def generate_tempo_expr_times(syntax_tempo_expr_objects, syntaxUserOp, genEqu):
    counter_name = syntaxUserOp.generate_name_for_tmp(postfix="counter")
    counter_symbol = SyntaxVariableSymbol(counter_name, False, False)
    counter_symbol.isOutput = True
    counter_symbol.syntaxType = SyntaxType("int32")
    syntaxUserOp.add_tmpSymbol(counter_symbol)
    # preCode分为两部分，先根据init决定是否初始化，根据输入的布尔值决定是否自减
    # counter_name需要加入到outC之中
    depth = genEqu.depth
    int_expr = syntax_tempo_expr_objects[0]
    bool_expr = syntax_tempo_expr_objects[1]
    # 根据init初始化
    pre_code = f"{'    ' * depth}kcg_int32 {counter_name};\n"
    pre_code += f"{'    ' * depth}if (outC->{syntaxUserOp.initSymbol}){{\n" \
                f"{'    ' * (depth + 1)}{counter_name} = {SyntaxExpr_generate(int_expr, syntaxUserOp, genEqu)};\n" \
                f"{'    ' * depth}}}\n" \
                f"{'    ' * depth}else {{\n" \
                f"{'    ' * (depth + 1)}{counter_name} = outC->{counter_name};\n" \
                f"{'    ' * depth}}}\n"
    # 根据bool值进行自减，若已经小于0了就不变，然后如果bool为true则减一，如果为false则不变
    pre_code += f"{'    ' * depth}if ({counter_name}<kcg_lit_int32(0)) {{\n" \
                f"{'    ' * (depth + 1)}outC->{counter_name} = {counter_name};\n" \
                f"{'    ' * depth}}}\n" \
                f"{'    ' * depth}else if ({SyntaxExpr_generate(bool_expr, syntaxUserOp, genEqu)}){{\n" \
                f"{'    ' * (depth + 1)}outC->{counter_name} = {counter_name} - kcg_lit_int32(1);\n" \
                f"{'    ' * depth}}}\n" \
                f"{'    ' * depth}else {{\n" \
                f"{'    ' * (depth + 1)}outC->{counter_name} = {counter_name};\n" \
                f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    # 返回的代码为当前countern是否为0

    out_code = f"({SyntaxExpr_generate(bool_expr, syntaxUserOp, genEqu)}&(outC->{counter_name} == kcg_lit_int32(0)))"
    return out_code


@register_tempo_expr_hander("WHEN")
def generate_tempo_expr_when(syntax_tempo_expr_objects, syntaxUserOp, genEqu):
    pass


@register_tempo_expr_hander("MERGE")
def generate_tempo_expr_merge(syntax_tempo_expr_objects, syntaxUserOp, genEqu):
    pass


generate_switch_expr_handlers = {}


def register_switch_expr_handler(type_):
    def decorator(func):
        generate_switch_expr_handlers[type_] = func
        return func

    return decorator


@register_switch_expr_handler("IF")
def generate_switch_expr_if(syntax_switch_expr_objects, syntaxUserOp, genEqu):
    return f"({SyntaxExpr_generate(syntax_switch_expr_objects[0], syntaxUserOp, genEqu)} ? {SyntaxExpr_generate(syntax_switch_expr_objects[1], syntaxUserOp, genEqu)} : {SyntaxExpr_generate(syntax_switch_expr_objects[2], syntaxUserOp, genEqu)})"


@register_switch_expr_handler("CASE")
def generate_switch_expr_case(syntax_switch_expr_objects, syntaxUserOp, genEqu):
    tmp_var_name = syntaxUserOp.generate_name_for_tmp()
    tmp_var_symbol = SyntaxVariableSymbol(tmp_var_name, False, False)
    tmp_var_symbol.syntaxType = SyntaxType(lhs_type)
    syntaxUserOp.add_tmpSymbol(tmp_var_symbol)
    pre_equations = f"switch({SyntaxExpr_generate(syntax_switch_expr_objects[0], syntaxUserOp, genEqu)}){{\n"
    for elem in syntax_switch_expr_objects[1]:
        syntaxPattern = elem[0]
        syntaxExpr = elem[1]
        if syntaxPattern.type != '_':
            pre_equations += f"case {syntaxPattern.value}:\n {tmp_var_name} = {SyntaxExpr_generate(syntaxExpr, syntaxUserOp, genEqu)};\nbreak;\n"
        else:
            pre_equations += f"default:\n {tmp_var_name} = {SyntaxExpr_generate(syntaxExpr, syntaxUserOp, genEqu)};\nbreak;\n"
    pre_equations += "}\n"
    genEqu.preEquations.append(pre_equations)
    return tmp_var_name


generate_bool_expr_handlers = {}


def register_bool_expr_handler(type_):
    def decorator(func):
        generate_bool_expr_handlers[type_] = func
        return func

    return decorator


@register_bool_expr_handler("NOT")
def generate_bool_expr_not(syntax_bool_expr_objects, syntaxUserOp, genEqu):
    return f"( !({SyntaxExpr_generate(syntax_bool_expr_objects[0], syntaxUserOp, genEqu)}) )"


@register_bool_expr_handler("HASHTAG")
def generate_bool_expr_hashtag(syntax_bool_expr_objects, syntaxUserOp, genEqu):
    code = "(("
    for idx, obj in enumerate(syntax_bool_expr_objects[0]):
        if idx != 0:
            code += "+"
        code += SyntaxExpr_generate(obj, syntaxUserOp, genEqu)
    code += ") <= 1)"
    return code


@register_bool_expr_handler("binOp")
def generate_bool_expr_binop(syntax_bool_expr_objects, syntaxUserOp, genEqu):
    binOp_dict = {"and": " & ", "or": " | ", "xor": " ^ "}
    return f"({SyntaxExpr_generate(syntax_bool_expr_objects[0], syntaxUserOp, genEqu)}{binOp_dict[syntax_bool_expr_objects[1]]}{SyntaxExpr_generate(syntax_bool_expr_objects[2], syntaxUserOp, genEqu)})"


generate_atom_expr_handlers = {}


def register_atom_expr_handler(type_):
    def decorator(func):
        generate_atom_expr_handlers[type_] = func
        return func

    return decorator


@register_atom_expr_handler("bool_atom")
def generate_atom_expr_bool(syntax_atom_expr_objects, syntaxUserOp, genEqu):
    return f"kcg_{syntax_atom_expr_objects[0]}"


@register_atom_expr_handler("integernum")
def generate_atom_expr_integernum(syntax_atom_expr_objects, syntaxUserOp, genEqu):
    return syntax_atom_expr_objects[0]


@register_atom_expr_handler("floatnum")
def generate_atom_expr_floatnum(syntax_atom_expr_objects, syntaxUserOp, genEqu):
    return syntax_atom_expr_objects[0]


@register_atom_expr_handler("character")
def generate_atom_expr_character(syntax_atom_expr_objects, syntaxUserOp, genEqu):
    return syntax_atom_expr_objects[0]


@register_atom_expr_handler("typed_integer")
def generate_atom_expr_typed_integer(syntax_atom_expr_objects, syntaxUserOp, genEqu):
    return ""


@register_atom_expr_handler("typed_float")
def generate_atom_expr_typed_float(syntax_atom_expr_objects, syntaxUserOp, genEqu):
    return ""


generate_relation_expr_handlers = {}


def register_relation_expr_handler(type_):
    def decorator(func):
        generate_relation_expr_handlers[type_] = func
        return func

    return decorator


@register_relation_expr_handler('Relation_expr')
def generate_relation_expr(syntax_relation_expr_objects, syntaxUserOp, genEqu):
    op = syntax_relation_expr_objects[1]
    if op == '<>':
        op = '!='
    elif op == '=':
        op = '=='
    return f"({SyntaxExpr_generate(syntax_relation_expr_objects[0], syntaxUserOp, genEqu)} {op} {SyntaxExpr_generate(syntax_relation_expr_objects[2], syntaxUserOp, genEqu)})"


generate_arith_expr_handlers = {}


def register_arith_expr_handler(type_):
    def decorator(func):
        generate_arith_expr_handlers[type_] = func
        return func

    return decorator


@register_arith_expr_handler('cast')
def generate_arith_expr_cast(syntax_arith_expr_objects, syntaxUserOp, genEqu):
    syntax_type = syntax_arith_expr_objects[1]
    expr = syntax_arith_expr_objects[0]
    return f"{(syntax_type.change_name())}({SyntaxExpr_generate(expr, syntaxUserOp, genEqu)})"


@register_arith_expr_handler('unary')
def generate_arith_expr_unary(syntax_arith_expr_objects, syntaxUserOp, genEqu):
    unary_op = syntax_arith_expr_objects[0]
    if unary_op == '+':
        return f"({SyntaxExpr_generate(syntax_arith_expr_objects[1], syntaxUserOp, genEqu)})"
    elif unary_op == '-':
        return f"{unary_op}({SyntaxExpr_generate(syntax_arith_expr_objects[1], syntaxUserOp, genEqu)})"
    else:  # lnot需要在中间层转化为lnot_uXX,先用uint64替代，等Expr的exprType得到可以将其替换
        return f"kcg_lnot_uint64({SyntaxExpr_generate(syntax_arith_expr_objects[1], syntaxUserOp, genEqu)})"


@register_arith_expr_handler('binOp')
def generate_arith_expr_binOp(syntax_arith_expr_objects, syntaxUserOp, genEqu):
    # 此处var_type需要等Expr的exprType设置完进行替换
    if syntax_arith_expr_objects[1] == 'lsl':
        var_type = "uint64"
        return f"kcg_lsl_{var_type}({SyntaxExpr_generate(syntax_arith_expr_objects[0], syntaxUserOp, genEqu)},{SyntaxExpr_generate(syntax_arith_expr_objects[2], syntaxUserOp, genEqu)})"
    else:
        binop_dict = {"+": "+", "-": "-", "*": "*", "/": "/", "mod": "%", "land": "&", "lor": "|", "lxor": "^",
                      "lsr": ">>"}
        return f"{SyntaxExpr_generate(syntax_arith_expr_objects[0], syntaxUserOp, genEqu)} {binop_dict[syntax_arith_expr_objects[1]]} {SyntaxExpr_generate(syntax_arith_expr_objects[2], syntaxUserOp, genEqu)}"


generate_id_expr_handlers = {}


def register_id_expr_handler(type_):
    def decorator(func):
        generate_id_expr_handlers[type_] = func
        return func

    return decorator


@register_id_expr_handler("Path_id")
def generate_id_expr_path_id(syntax_id_expr_objects, syntaxUserOp, genEqu):
    # TODO:如果path_id是包含“::”的路径名，生成代码时需要将::替换为_，需要修改路径的顺序
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
def generate_id_expr_single_quote_lv6id(syntax_id_expr_objects, syntaxUserOp, genEqu):
    # 把signal的第一个字符也就是'去掉
    return syntax_id_expr_objects[0][1:]


@register_id_expr_handler("lastSinglequoteLv6id")
def generate_id_expr_last_single_quote_lv6id(syntax_id_expr_objects, syntaxUserOp, genEqu):
    """last的情况总是记录这个值上个周期的值，在状态机外与pre相同，在状态机内，pre会读出目标变量在这个状态内上次改变的值"""
    # 向outC中新添加一个变量
    # 例如b=last 'a,添加tmp_a，句子变成：
    # b=outC->tmp_a;outC->tmp_a=a;
    target_name = syntax_id_expr_objects[0][1:]
    target_var = syntaxUserOp.get_localVariable_InThisAndPreEnv(target_name)
    if not target_var:
        raise UnknownIdentifierException(f"在{syntaxUserOp.get_global_name()}中找不到{target_name}")

    tmp_var_name = syntaxUserOp.generate_name_for_tmp(postfix=f"{target_name}_mem_last")
    tmp_var = SyntaxVariableSymbol(tmp_var_name, False, False)
    tmp_var.syntaxType = target_var.syntaxType
    tmp_var.isOutput = True
    tmp_var.postExpr = SyntaxExpr(type="Id_expr", subtype="Path_id")
    tmp_var.postExpr.add_object(target_name)
    syntaxUserOp.add_tmpSymbol(tmp_var)

    out_name = syntaxUserOp.var_change_name(tmp_var_name)
    return out_name


@register_id_expr_handler("ID")
def generate_id_expr_ID(syntax_id_expr_objects, syntaxUserOp, genEqu):
    return syntax_id_expr_objects[0]


generate_expr_handlers = {}


def register_expr_handler(type_):
    def decorator(func):
        generate_expr_handlers[type_] = func
        return func

    return decorator


@register_expr_handler('Id_expr')
def generate_Id_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_id_expr_handler = generate_id_expr_handlers.get(subtype_)
    if generate_id_expr_handler:
        return generate_id_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Id_expr , subtype:{subtype_}")


@register_expr_handler('Atom')
def generate_Atom_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_atom_expr_handler = generate_atom_expr_handlers.get(subtype_)
    if generate_atom_expr_handler:
        return generate_atom_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Atom_expr , subtype:{subtype_}")


@register_expr_handler('Tempo_expr')
def generate_Tempo_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_tempo_expr_handler = generate_tempo_expr_handlers.get(subtype_)
    if generate_tempo_expr_handler:
        return generate_tempo_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Tempo_expr , subtype:{subtype_}")


@register_expr_handler('Arith_expr')
def generate_Arith_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_arith_expr_handler = generate_arith_expr_handlers.get(subtype_)
    if generate_arith_expr_handler:
        return generate_arith_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Arith_expr , subtype:{subtype_}")


@register_expr_handler('Relation_expr')
def generate_Relation_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_relation_expr_handler = generate_relation_expr_handlers.get(subtype_)
    if generate_relation_expr_handler:
        return generate_relation_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Relation_expr , subtype:{subtype_}")


@register_expr_handler('List_expr')
def generate_List_expr(syntaxExpr, syntaxUserOp, genEqu):
    # 长度只可能为1，lnot(in1),此处会使用list。list在中间层会被拆开。
    return SyntaxExpr_generate(syntaxExpr.objects[0][0], syntaxUserOp, genEqu)


@register_expr_handler('Switch_expr')
def generate_Switch_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_switch_expr_handler = generate_switch_expr_handlers.get(subtype_)
    if generate_switch_expr_handler:
        return generate_switch_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Switch_expr , subtype:{subtype_}")


@register_expr_handler('Bool_expr')
def generate_Bool_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_bool_expr_handler = generate_bool_expr_handlers.get(subtype_)
    if generate_bool_expr_handler:
        return generate_bool_expr_handler(syntaxExpr.objects, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Bool_expr , subtype:{subtype_}")


@register_expr_handler('Struct_expr')
def generate_Struct_expr(syntaxExpr, syntaxUserOp, genEqu):
    return ""


@register_expr_handler('Array_expr')
def generate_Array_expr(syntaxExpr, syntaxUserOp, genEqu):
    return ""


@register_expr_handler('Apply_expr')
def generate_Apply_expr(syntaxExpr, syntaxUserOp, genEqu):
    return ""


@register_expr_handler('Mixed_constructor')
def generate_Mixed_constructor(syntaxExpr, syntaxUserOp, genEqu):
    return ""


def SyntaxExpr_generate(syntaxExpr, syntaxUserOp, genEqu):
    type_ = syntaxExpr.type
    generate_expr_handler = generate_expr_handlers.get(type_)
    if generate_expr_handler:
        return generate_expr_handler(syntaxExpr, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"Unknown type: {type_}")


generate_userOp_handlers = {}


def register_userOp_handler(type_):
    def decorator(func):
        generate_userOp_handlers[type_] = func
        return func

    return decorator


@register_userOp_handler("simple_equation")
def generate_userOp_simple_equation(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    # out1=in1;若out1是数组或结构体，则需要使用memcpy，不能使用=。若右边是函数调用，且返回多个值，也不能直接使用=
    global lhs_type
    if syntaxEquation.lhs[0]=="_":return""
    lhs_symbol = syntaxUserOp.get_localVariable_InThisAndPreEnv(syntaxEquation.lhs[0])
    if lhs_symbol is None: lhs_symbol = syntaxUserOp.get_tmpSymbol(syntaxEquation.lhs[0])
    lhs_type = lhs_symbol.syntaxType.type
    genEqu = GenEqu(depth)
    genEqu.expr = SyntaxExpr_generate(syntaxEquation.expr, syntaxUserOp, genEqu)
    code = ""
    code += "".join(genEqu.preEquations)
    code += f"{'    ' * depth}{syntaxUserOp.var_change_name(syntaxEquation.lhs[0])} = {genEqu.expr};\n"
    code += "".join(genEqu.postEquations)
    return code


@register_userOp_handler("assume")
def generate_userOp_assume(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    return ""


@register_userOp_handler("guarantee")
def generate_userOp_guarantee(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    return ""


@register_userOp_handler("emission")
def generate_userOp_emission(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    code = ""
    for signal in syntaxEquation.lhs:
        code += f"{signal} = kcg_true;\n"
    return code


@register_userOp_handler("control_block")
def generate_userOp_control_block(syntaxEquation, syntaxUserOp, code_generator, depth=1):
    control_block_ID = syntaxEquation.controlBlockID
    control_block = syntaxUserOp.get_childScope(control_block_ID)
    if control_block is None: raise UnknownIdentifierException(f"control_block {control_block_ID} 没有找到")
    # print("this is control_block", syntaxEquation.controlBlockID)
    if control_block.type == "automaton":

        code_generator.add_code_to_types_file(automaton_generate.generate_type(control_block))
        # print("HEAD:")
        # print(automaton_generate.generate_state_nxt_for_head(control_block))
        # print("INIT:")
        # print(automaton_generate.generate_init_symbol_for_init(control_block))

        return automaton_generate.generate_body(control_block, code_generator, depth)
    else:
        return ""  # 这里是if和elseblock的部分


def SyntaxUserOp_generate(syntaxUserOp, code_generator):
    code = ""
    for elem in syntaxUserOp.equations:
        type_ = elem.type
        generate_userOp_handler = generate_userOp_handlers.get(type_)
        if generate_userOp_handler:
            code += generate_userOp_handler(elem, syntaxUserOp, code_generator)
        else:
            raise ValueError(f"syntaxUserOp_generate error , type : {type_}")
    print("=== UserOp ===\n")
    print(code)
    print("==========")
    return code


generate_syntax_type_handlers = {}


def register_syntax_type_handler(pattern):
    def decorator(func):
        generate_syntax_type_handlers[re.compile(pattern)] = func
        return func

    return decorator


@register_syntax_type_handler(r"^signed")
def generate_syntax_type_signed(typeSymbol, rootPackage):
    genEqu = GenEqu()
    size = SyntaxExpr_generate(typeSymbol.syntaxType.sizeExpr, rootPackage, genEqu)
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.name if len(global_name) == 0 else f"{typeSymbol.name}_{global_name}"
    code = f"typedef kcg_int{size} {var_name};\n"
    print("=== signed ===\n")
    print(code)
    return code


@register_syntax_type_handler(r"^unsigned")
def generate_syntax_type_unsigned(typeSymbol, rootPackage):
    genEqu = GenEqu()
    size = SyntaxExpr_generate(typeSymbol.syntaxType.sizeExpr, rootPackage, genEqu)
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.name if len(global_name) == 0 else f"{typeSymbol.name}_{global_name}"
    code = f"typedef kcg_uint{size} {var_name};\n"
    print("=== unsigned ===\n")
    print(code)
    return code


@register_syntax_type_handler(r"^path_id")
def generate_syntax_type_path_id(typeSymbol, rootPackage):
    print("this is path_id", typeSymbol.syntaxType.value)
    return ""


@register_syntax_type_handler(r"^typevar")
def generate_syntax_type_typevar(typeSymbol, rootPackage):
    print("this is typevar", typeSymbol.syntaxType.value)
    return ""


@register_syntax_type_handler(r"^enum")
def generate_syntax_type_enum(typeSymbol, rootPackage):
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.name if len(global_name) == 0 else f"{typeSymbol.name}_{global_name}"
    code = f"typedef enum {var_name} {{\n"
    for idx, enum_elem in enumerate(typeSymbol.syntaxType.enumList):
        if idx != 0:
            code += ",\n"
        code += f"{enum_elem}" if len(global_name) == 0 else f"{enum_elem}_{global_name}"
    code += f"\n}} {var_name};\n"
    print("=== enum ===")
    print(code)
    return code


@register_syntax_type_handler(r"^field_decl")
def generate_syntax_type_field_decl(typeSymbol, rootPackage):
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.name if len(global_name) == 0 else f"{typeSymbol.name}_{global_name}"
    precode = ""
    code = f"typedef struct {var_name} {{\n"
    for k, v in typeSymbol.syntaxType.fields.items():
        if v.type in v.basic_type:
            code += f"kcg_{v.type} {k};\n"
        else:
            tmpTypeSymbol = SyntaxTypeSymbol(f"tmp_struct_{k}", "public")
            tmpTypeSymbol.syntaxType = v
            precode = generate_type_symbol(tmpTypeSymbol, rootPackage)
            tmpName = f"tmp_struct_{k}" if len(global_name) == 0 else f"tmp_struct_{k}_{global_name}"
            code += f"{tmpName} {k};\n"
    code += f"\n}} {var_name};\n"
    code = precode + code
    return code


def generate_syntax_type_list_recursive(syntaxType, rootPackage, symbolName):
    if syntaxType.type not in syntaxType.basic_type:
        type_, code_ = generate_syntax_type_list_recursive(syntaxType.listType, rootPackage, symbolName)
        genEqu = GenEqu()
        size_ = SyntaxExpr_generate(syntaxType.listExpr, rootPackage, genEqu)
        name_ = f"{symbolName}_array_{size_}"
        code_ += f"typedef {type_} {name_}[{size_}];\n"
        return name_, code_
    else:
        code_ = f"kcg_{syntaxType.type}"
        return code_, ""


@register_syntax_type_handler(r"^list")
def generate_syntax_type_list(typeSymbol, rootPackage):
    print("this is list ", typeSymbol.name, type(typeSymbol.syntaxType.listExpr), type(typeSymbol.syntaxType.listType),
          typeSymbol.syntaxType.listType)
    type_, code_ = generate_syntax_type_list_recursive(typeSymbol.syntaxType, rootPackage, typeSymbol.name)
    code_ += f"typedef {type_} {typeSymbol.name};\n"
    print("==== code_\n")
    print(code_)
    return code_


@register_syntax_type_handler(r"(bool|char|int\d+|uint\d+|float\d+)")
def generate_syntax_type_other(typeSymbol, rootPackage):
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.name if len(global_name) == 0 else f"{typeSymbol.name}_{global_name}"
    code = f"typedef {typeSymbol.syntaxType.change_name()} {var_name};\n"
    print("=== other ===")
    print(code)
    return code


def write_file_from_src_to_target(src, target):
    with open(src, 'r') as src_file:
        content = src_file.read()
    with open(target, 'w') as target_file:
        target_file.write(content)


def write_file(file_path, content, mode):
    with open(file_path, mode) as target_file:
        target_file.write(content)


def generate_const_equation(rootPackage):
    h_content = ""
    c_content = ""
    for _, packageScope in rootPackage.childScopeTable.items():
        h, c = generate_const_equation(packageScope)
        h_content += h
        c_content += c
    global_name = rootPackage.get_global_name()
    for name, constSymbol in rootPackage.constSymbolTable.items():
        symbol_name = name if len(global_name) == 0 else f"{name}_{global_name}"
        symbol_type = constSymbol.syntaxType.change_name()
        if constSymbol.isImported == True:
            h_content += f'''
            #ifndef {symbol_name}\n
            #define {symbol_name} {symbol_name}\n
            extern const {symbol_type} {symbol_name};\n
            #endif\n
           '''
        else:
            h_content += f"extern const {symbol_type} {symbol_name};\n"
            c_content += f"const {symbol_type} {symbol_name}={SyntaxExpr_generate(constSymbol.valueExpr, rootPackage, symbol_type)};\n"
    return h_content, c_content


def generate_type_symbol(typeSymbol, rootPackage):
    type_ = typeSymbol.syntaxType.type
    for regex, func in generate_syntax_type_handlers.items():
        if regex.match(type_):
            return func(typeSymbol, rootPackage)


def generate_type_block(rootPackage):
    h_content = ""
    for _, packageScope in rootPackage.childScopeTable.items():
        h_content += generate_type_block(packageScope)
    for _, typeSymbol in rootPackage.typeSymbolTable.items():
        h_content += generate_type_symbol(typeSymbol, rootPackage)
    return h_content


def generate_data_def(data_def: SyntaxDataDefScope, code_generator: GenerateCode, depth=0) -> str:
    """给所有继承了data_def类的作用域生成代码，user_op除外，用genrateCode里面的函数"""
    # localVariable + tmpVariable
    decl_content = ""
    src_content = ""
    post_content = ""
    for elem in data_def.equations:
        type_ = elem.type
        generate_userOp_handler = generate_userOp_handlers.get(type_)
        if generate_userOp_handler:
            src_content += generate_userOp_handler(elem, data_def, code_generator, depth)
        else:
            raise ValueError(f"syntaxUserOp_generate error , type : {type_}")
    for name, symbol in data_def.localSymbolTable.items():
        decl_content += f"{'    ' * depth}{symbol.syntaxType.change_name()} {name};\n"
    for signal in data_def.signalSymbolSet:
        decl_content += f"{'    ' * depth}kcg_bool {signal};\n"
    for paraSymbol in data_def.tmpParams:
        if paraSymbol.isOutput == False:
            decl_content += f"{'    ' * depth}{paraSymbol.syntaxType.change_name()} {paraSymbol.name};\n"
        if paraSymbol.postExpr != None:
            genEqu = GenEqu()
            if len(genEqu.preEquations) != 0: post_content += f"{'    ' * depth}"
            post_content += f"{'    ' * depth}".join(genEqu.preEquations)
            post_content += f"{'    ' * depth}{data_def.var_change_name(paraSymbol.name)} = {SyntaxExpr_generate(paraSymbol.postExpr, data_def, genEqu)};\n"
            if len(genEqu.postEquations) != 0: post_content += f"{'    ' * depth}"
            post_content += f"{'    ' * depth}".join(genEqu.postEquations)
    content = decl_content+src_content+post_content
    return content


def scade_generate(root_operator, code_generator: GenerateCode):
    for k, v in root_scope.userOpTable.items():
        SyntaxUserOp_generate(v, code_generator)


def scade_parse(input_path: str, main_operator: str, output_path: str):
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

    post_process(root_scope)

    gen = GenerateCode(root_scope, main_operator, output_path)
    gen.generate_const_file()
    # gen.generate_main_file()
    gen.generate_types_file()
    stack = deque([root_scope])
    while stack:
        tar_package=stack.pop()
        for k, v in tar_package.userOpTable.items():
            gen.generate_node_file(v)
            # gen.generate_head_file(v)
            # gen.generate_src_file(v)
        for k,sub_package in tar_package.childScopeTable.items():
            stack.append(sub_package)

    # scade_generate(main_operator)
    gen.add_code_to_types_file("#endif\n")  # 结束


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-m', '--main_operator', required=True, type=str)
    argParser.add_argument('-o', '--output_path', required=True, type=str)
    args = argParser.parse_args()
    scade_parse(args.input_path, args.main_operator, args.output_path)
