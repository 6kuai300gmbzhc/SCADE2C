import os.path
from collections import deque

from syntax_tree.SyntaxClass import *
from syntax_tree.scade_preprocess import *
from syntax_tree.scade_postprocess import post_process
from functools import wraps
from syntax_tree.scade_const_expression import cal_const_expr

import syntax_tree.automaton_generate as automaton_generate


class GenerateCode:
    def __init__(self, rootNode, mainNode, outputDir):
        self.rootNode = rootNode
        self.mainNode = mainNode
        self.outputDir = outputDir
        self.specialTypes = set()  # 保存了需要手动加入type文件的类型，比如数组,存str
        self.importedFunctions: set[SyntaxUserOp] = set()  # 保存了

        if not os.path.isdir(self.outputDir):
            os.makedirs(self.outputDir)
        mainNode = self.mainNode.split("::")
        self.outputDir = f"{outputDir}/{mainNode[-1]}" if len(
            mainNode) == 1 else f"{outputDir}/{mainNode[-1]}_{'_'.join(mainNode[:-1])}"
        if not os.path.exists(f"{self.outputDir}/src"): os.makedirs(f"{self.outputDir}/src")
        if not os.path.exists(f"{self.outputDir}/include"): os.makedirs(f"{self.outputDir}/include")

    def generate_const_file(self):
        # 只要写了const_block无论是否使用都会使用,从root_node开始深度遍历
        # 改了，没用到的没有生成进去
        c_content = '''#include "kcg_consts.h"\n'''
        c_content += '#ifndef _KCG_CONSTS_C_\n' \
                     '#define _KCG_CONSTS_C_\n'
        h_content = '''#ifndef _KCG_CONSTS_H_\n#define _KCG_CONSTS_H_\n#include "kcg_types.h"\n'''

        h, c = generate_const_equation(self.rootNode)
        h_content += h
        c_content += c

        h_content += '''#endif'''
        c_content += '''#endif'''
        # print("==== h_content ====\n",h_content)
        # print("==== c_content ====\n",c_content)
        # write_file(f"{self.outputDir}/include/kcg_consts.h",h_content,"w")
        # write_file(f"{self.outputDir}/src/kcg_consts.c",c_content,"w")
        with open("%s/../kcg_consts.h" % (self.outputDir), 'w') as f:
            f.write(h_content)
        with open("%s/../kcg_consts.c" % (self.outputDir), 'w') as f:
            f.write(c_content)

    def generate_sensor_file(self):
        pass

    def generate_types_file(self):
        src_file = "./template/kcg_types.h"
        target_file = f"{self.outputDir}/../kcg_types.h"
        # write_file_from_src_to_target(src_file,target_file)

        # 中间还需要写和types相关的内容
        with open(target_file, 'w') as target:
            with open(src_file, 'r') as src:
                target.write(src.read())
            target.write(generate_type_block(self.rootNode))

    def add_code_to_types_file(self, code: str):
        target_file = f"{self.outputDir}/../kcg_types.h"
        with open(target_file, "a") as target:
            target.write(code)

    # write_file(target_file,content,"a")

    def generate_assign_file(self):
        src_file = "../template/kcg_assign.h"
        target_file = f"{self.outputDir}/../kcg_assign.h"
        # write_file_from_src_to_target(src_file,target_file)

    def generate_imported_types_file(self):
        pass

    @staticmethod
    def generate_imported_function_name(imported_op: SyntaxUserOp) -> str:
        package_name = imported_op.get_my_package().name
        op_name = imported_op.name
        return f"{op_name}_{package_name}_{package_name}impl"

    def generate_imported_functions_file(self):
        def generate_imported_function_decl(imported_op: SyntaxUserOp) -> str:
            # 输出只有一个值，要不然就不是宏了
            out_type_code = imported_op.outParams[0].syntaxType.change_name()
            input_code = ", ".join(
                [f"{in_param.syntaxType.change_name()} {in_param.name}" for in_param in imported_op.inParams])

            decl = f"extern {out_type_code} {self.generate_imported_function_name(imported_op)}({input_code});\n"
            return decl

        code = f"#ifndef KCG_IMPORTED_FUNCTIONS_H_\n" \
               f"#define KCG_IMPORTED_FUNCTIONS_H_\n" \
               f'#include "kcg_types.h"\n'
        for imported_op in self.importedFunctions:
            code += generate_imported_function_decl(imported_op)
        code += "#endif"

        target_file = f"{self.outputDir}/../kcg_imported_functions.h"
        with open(target_file, 'w') as target:
            target.write(code)

    def generate_macro_libmathext_file(self):
        path_dict = {"../template/macro_libmathext32.h": f"{self.outputDir}/../macro_libmathext32.h",
                     "../template/macro_libmathext64.h": f"{self.outputDir}/../macro_libmathext64.h"}
        for k, v in path_dict.items():
            write_file_from_src_to_target(k, v)

    def generate_head_inC(self, node):
        global_name = node.get_global_name()
        code = "typedef struct{\n"
        for para in node.inParams:
            code += f"    {para.syntaxType.change_name()} {para.name};\n"
        code += f"}}{node.get_inC_name()};\n"
        return code

    def generate_head_outC(self, node):
        code = "typedef struct{\n"
        # outparams
        # tmpparams里需要output的
        # 调用的函数上下文
        # 状态机的state_nxt
        # 这里要将node及其以下的所有子作用域的out情况都统计进来
        # 所以写一个深度优先搜索吧
        stack = deque()
        stack.append(node)
        # 只有最上层的状态机需要登记outC，其他不需要
        # 只有userOP有outParams，也就是最上层节点
        for para in node.outParams:
            code += f"    {para.syntaxType.change_name()} {para.name};\n"
        for applied_expr in node.apply_exprs:
            if not applied_expr.appliedOp.hasInternalState: continue
            size_decl = ""
            if applied_expr.appliedOpContextList:
                size_decl = f"[{']['.join(map(str, applied_expr.appliedOpContextList))}]"
            code += f"    {applied_expr.appliedOp.get_outC_name()} {applied_expr.appliedOpOutCName}{size_decl};\n"
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

        code += f"}}{node.get_outC_name()};\n"
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

    def generate_head_include(self, node):
        """若有函数调用，自动include"""
        code = ""
        had_imported_function = False
        for applied_expr in node.apply_exprs:
            applied_op = applied_expr.appliedOp
            if applied_op.isImported:
                if not had_imported_function:
                    code += '#include "macro_libmathext32.h"\n'
                    code += '#include "macro_libmathext64.h"\n'
                had_imported_function = True
                self.importedFunctions.add(applied_op)

            if applied_op.hasInternalState:
                code += f'#include "{applied_expr.appliedOp.get_global_name()}.h"\n'
        return code

    def generate_head_file(self, node):
        global_name = node.get_global_name()
        head_content = f'#ifndef _{global_name}_H_\n#define _{global_name}_H_\n#include"kcg_types.h"\n'
        head_content += self.generate_head_include(node)
        head_content += self.generate_head_inC(node)
        head_content += self.generate_head_outC(node)
        head_content += self.generate_head_func(node)
        head_content += self.generate_head_other_func(node)

        head_content += f"#endif"
        # print("==== head_content ====\n")
        # print(head_content)
        # print("=======================\n")
        target_file = f"{self.outputDir}/../{global_name}.h"
        with open(target_file, "w") as target:
            target.write(head_content)

    def generate_variable_decl(self, symbol, symbol_name, depth: int = 1):
        """生成类型声明代码"""
        symbol_type = symbol.syntaxType
        c_type_name = symbol_type.change_name()
        return f"{'    ' * depth}{c_type_name} {symbol_name};\n"

    def check_and_add_special_types(self, syntaxType: SyntaxType):
        """向types文件中添加特殊类型定义"""
        c_type_name = syntaxType.change_name()
        if syntaxType.get_real_type().type == "array":
            if c_type_name not in self.specialTypes:
                self.specialTypes.add(c_type_name)
                type_decl_code = f"typedef " \
                                 f"{syntaxType.get_element_type_for_array().change_name()} {c_type_name}[{syntaxType.get_size()}];\n"
                self.add_code_to_types_file(type_decl_code)
        else:
            # todo 加入其他的变量声明
            pass

    def generate_data_def(self, data_def: SyntaxDataDefScope, depth=0) -> str:
        """对data_def的代码生成
        应只有最基础的功能，即data_def只作为某个代码块出现
        包括了变量声明，一般的语句生成，init过程
        有变量声明就需要有init，因为需要在
        """
        # localVariable + tmpVariable
        decl_content = ""
        src_content = ""
        post_content = ""
        body_content = SyntaxUserOp_generate(data_def, self, depth)
        # 加入init判断
        if data_def.initVar:
            src_content += f"{'    ' * depth}if (outC->{data_def.initVar.name}){{\n"
            for tmpSymbol in data_def.tmpParams:
                if tmpSymbol.lastExpr and tmpSymbol.isOutput:
                    src_content += f"{'    ' * (depth + 1)}outC->{tmpSymbol.name} = {SyntaxExpr_generate(tmpSymbol.lastExpr, data_def, GenEqu())};\n"
            src_content += f"{'    ' * depth}}}\n"
        src_content += body_content
        if data_def.initVar:
            src_content += f"{'    ' * depth}outC->{data_def.initVar.name} = kcg_false;\n"
        for name, symbol in data_def.localSymbolTable.items():
            self.check_and_add_special_types(symbol.syntaxType)
            decl_content += self.generate_variable_decl(symbol, name, depth)
        for signal in data_def.signalSymbolSet:
            decl_content += f"{'    ' * depth}kcg_bool {signal};\n"
        for paraSymbol in data_def.tmpParams:
            self.check_and_add_special_types(paraSymbol.syntaxType)
            if paraSymbol.isOutput == False:
                decl_content += self.generate_variable_decl(paraSymbol, paraSymbol.name, depth)
            post_code = paraSymbol.postExpr
            if post_code:
                if not isinstance(post_code, list):
                    post_content += '    ' + post_code
                else:
                    post_content += '    ' + '    '.join(post_code)
        content = decl_content + src_content + post_content
        return content

    def generate_src_func_file(self, node):
        global_name = node.get_global_name()
        src_content = f"void {global_name}(inC_{global_name} *inC,outC_{global_name} *outC){{\n"
        src_content += self.generate_data_def(node, 1)
        src_content += f"}}\n"
        print("==== src_content ====\n")
        print(src_content)
        print("======================")
        return src_content

    def generate_src_init(self, node):
        # 如果是数组情况，就需要加循环
        def array_init(para_name, syntaxType, depth=0):
            _code = ""
            if syntaxType.type != "array":
                _code += f"{'    ' * (depth + 1)}{para_name} = {syntaxType.generate_init_expr()};\n"
            else:
                idx = "idx" if depth == 0 else f"idx_{str(depth)}"
                _code += f"{'    ' * (depth + 1)}for(kcg_size {idx}=0;{idx}<{syntaxType.get_size()};idx++){{\n" \
                         f"{array_init(f'{para_name}[{idx}]', syntaxType.get_element_type_for_array(), depth + 1)}" \
                         f"{'    ' * (depth + 1)}}}\n"
            return _code

        def generate_init_code(para: SyntaxVariableSymbol) -> str:
            if para.syntaxType.get_real_type().type == "array":
                return array_init(f"outC->{para.name}", para.syntaxType)
            if para.syntaxType.get_real_type().type == "field_decl":
                return ""
            return f"    outC->{para.name} = {para.syntaxType.generate_init_expr()};\n"

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
            code += generate_init_code(para)
        for applied_expr in node.apply_exprs:
            if not applied_expr.appliedOp.hasInternalState: continue
            depth = 1
            # todo 调用函数情况为数组的初始化过程，参考array初始化
            code += f"{'    ' * depth}{applied_expr.appliedOp.get_global_name()}_init(&(outC->{applied_expr.appliedOpOutCName}));\n"
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)
            if cur_node.type == "automaton":
                code += automaton_generate.generate_state_nxt_for_init(cur_node)

            for para in cur_node.tmpParams:
                if para.isOutput:
                    print("para init ", para.name)
                    code += generate_init_code(para)
        code += "}\n" \
                "#endif\n"
        return code

    def generate_src_reset(self, node):
        # 状态机回到初始
        # init变量为true
        # 递归reset其他函数
        global_name = node.get_global_name()
        code = "#ifndef KCG_NO_EXTERN_CALL_TO_RESET\n" \
               f"void {global_name}_reset(outC_{global_name} *outC)\n" \
               "{\n"
        # reset 其他函数
        for applied_expr in node.apply_exprs:
            if not applied_expr.appliedOp.hasInternalState: continue
            depth = 1
            # todo 调用函数情况为数组的reset过程，参考array初始化
            code += f"{'    ' * depth}{applied_expr.appliedOp.get_global_name()}_reset(&(outC->{applied_expr.appliedOpOutCName}));\n"
        # 最上层状态机回到初始状态
        # 重置init
        stack = deque()
        stack.append(node)
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)

            if cur_node.initVar:
                code += f"    outC->{cur_node.initVar.name} = kcg_true;\n"
        code += "}\n" \
                "#endif\n"
        return code

    def generate_src_file(self, node):
        global_name = node.get_global_name()
        src_content = f"#ifndef KCG_{node.get_global_name()}_C_\n#define KCG_{node.get_global_name()}_C_\n" \
                      f'#include "kcg_consts.c"\n#include "{global_name}.h"\n'
        # 然后include所调用的其他函数的头文件
        applied_functions = set()
        for apply_expr in node.apply_exprs:
            applied_op = apply_expr.appliedOp
            if applied_op in applied_functions: continue
            if applied_op.isImported: continue
            applied_functions.add(applied_op)
            src_content += f'''#include "{applied_op.get_global_name()}.c"\n'''
        src_content += self.generate_src_func_file(node)
        src_content += self.generate_src_init(node)
        src_content += self.generate_src_reset(node)
        src_content += '#endif'
        target_file = f"{self.outputDir}/../{global_name}.c"
        with open(target_file, "w") as target:
            target.write(src_content)

    def generate_node_file(self, node: SyntaxUserOp):
        if node.isImported: return
        self.generate_src_file(node)
        self.generate_head_file(node)

    def generate_test_file(self, main_node: SyntaxUserOp):
        """一个测试类"""
        import syntax_tree.testdata.generate_test_data as generate_test_data
        length = 100

        test_code = f'#include "stdio.h"\n' \
                    f'#include "kcg_types.h"\n' \
                    f'#include "{main_node.get_global_name()}.c"\n' \
                    f'#define true kcg_true\n' \
                    f'#define false kcg_false\n' \
                    f'int main(){{\n' \
                    f'    int length={length};\n' \
                    f'    {main_node.get_inC_name()} input;\n' \
                    f'    {main_node.get_outC_name()} output;\n' \
                    f'    {main_node.get_global_name()}_init(&output);\n'
        # 填充测试用例
        decls = ""
        fills_in = ""
        fills_out = ""
        generate_test_data.generate([p.syntaxType.get_real_type().type for p in main_node.inParams], main_node.name,
                                    length)
        with open(f"{self.outputDir}/../../../testdata/test_data_{main_node.name}_c.txt", "r") as test_data:
            for in_param in main_node.inParams:
                data = test_data.readline().strip("\n")
                decls += f'    {in_param.syntaxType.change_name()} {in_param.name}_list[] = {{{data}}};\n'
                fills_in += f'        input.{in_param.name}={in_param.name}_list[i];\n'
        for out_param in main_node.outParams:
            decls += f'    {out_param.syntaxType.change_name()} {out_param.name}_list[{str(length)}];\n'
            fills_out += f"        {out_param.name}_list[i]=output.{out_param.name};\n"
        test_code += decls
        test_code += "    for(int i=0;i<length;i++){\n"
        test_code += fills_in
        test_code += f'        {main_node.get_global_name()}(&input,&output);\n'
        test_code += fills_out
        test_code += '    }\n'
        test_code += f'    FILE *file = fopen("../../testdata/test_data_{main_node.name}_c_out.txt","w");\n'
        for out_param in main_node.outParams:
            test_code += f'    fprintf(file,"%s\\n","{out_param.name}");\n'
            test_code += "    for(int i=0;i<length;i++){\n"
            if out_param.syntaxType <= SyntaxType("float"):
                test_code += f'        fprintf(file,"%f, ",{out_param.name}_list[i]);\n'
            else:
                test_code += f'        fprintf(file,"%d, ",{out_param.name}_list[i]);\n'
            test_code += '    }\n'
            test_code += f'   fprintf(file,"\\n");\n'
        test_code += f'    fclose(file);\n' \
                     f'}}\n'

        file_name = f"{self.outputDir}/../test_{main_node.get_global_name()}.c"
        with open(file_name, "w") as file:
            file.write(test_code)


class GenEqu:
    expr: str
    '''可直接用于赋值的代码'''
    preEquations: list
    '''若需要使用到中间变量，中间变量的定义需要在该equation之前，是一个列表，列表里的元素是一个C语句'''

    depth: int
    '''这个语句所需要的缩进，默认是0'''

    def __init__(self, depth=0):
        self.expr = ""
        self.preEquations = []
        self.depth = depth

    def add_preEquations(self, equations):
        self.preEquations.append(equations)

    def __str__(self):
        code = ""
        code += "".join(self.preEquations)
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
def generate_tempo_expr_arrow(syntaxExpr, syntaxUserOp, genEqu):
    init_var = syntaxUserOp.set_init_var()
    code_ = f"({syntaxUserOp.var_change_name(init_var.name)} ? ({SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu)}) : ({SyntaxExpr_generate(syntaxExpr.objects[1], syntaxUserOp, genEqu)}))"
    print("arrow set_init_var", len(syntaxUserOp.tmpParams), syntaxUserOp.name)
    # print("arrow set_init_var",syntaxUserOp.tmpParams)
    for elem in syntaxUserOp.tmpParams:
        print("===", elem.name)
    return code_


@register_tempo_expr_hander("PRE")
def generate_tempo_expr_pre(syntaxExpr, syntaxUserOp, genEqu):
    tmp_var, tmp_var_name = generate_tmp_symbol_and_register(syntaxUserOp, syntaxExpr.lhsTypeList[0])
    tmp_var.isOutput = True
    tmp_var.postExpr = f"{syntaxUserOp.var_change_name(tmp_var_name)} = {SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu)};\n"
    return syntaxUserOp.var_change_name(tmp_var_name)


@register_tempo_expr_hander("FBY")
def generate_tempo_expr_fby(syntaxExpr, syntaxUserOp, genEqu):
    idxVar, tmp_idx_var_name = generate_tmp_symbol_and_register(syntaxUserOp, SyntaxType("int32"), "idx")
    idxVar.isOutput = True

    arrSyntaxType = SyntaxType("array")
    arrSyntaxType.sizeExpr = syntaxExpr.objects[1]
    arrSyntaxType.arrayType = syntaxExpr.lhsTypeList[0]
    arrSyntaxType.arrayType.scope = syntaxUserOp

    arrVar, tmp_arr_var_name = generate_tmp_symbol_and_register(syntaxUserOp, arrSyntaxType, "arr")
    arrVar.isOutput = True

    initVar = syntaxUserOp.set_init_var()

    depth = genEqu.depth
    preCode = f"{'    ' * depth}if({syntaxUserOp.var_change_name(initVar.name)}){{\n" \
              f"{'    ' * (depth + 1)}for(int idx=0;idx<{arrSyntaxType.get_size()};idx++){{\n" \
              f"{'    ' * (depth + 2)}{syntaxUserOp.var_change_name(tmp_arr_var_name)}[idx] = {SyntaxExpr_generate(syntaxExpr.objects[2], syntaxUserOp, genEqu)};\n" \
              f"{'    ' * (depth + 1)}}}\n" \
              f"{'    ' * (depth + 1)}{syntaxUserOp.var_change_name(tmp_idx_var_name)} = 0;\n" \
              f"{'    ' * depth}}}\n"
    postCode = [
        f"{syntaxUserOp.var_change_name(tmp_arr_var_name)}[{syntaxUserOp.var_change_name(tmp_idx_var_name)}]={SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu)};\n",
        f"{syntaxUserOp.var_change_name(tmp_idx_var_name)}=({syntaxUserOp.var_change_name(tmp_idx_var_name)}+1)%({arrSyntaxType.get_size()});\n"]
    arrVar.postExpr = postCode
    genEqu.add_preEquations(preCode)

    return f"{syntaxUserOp.var_change_name(tmp_arr_var_name)}[{syntaxUserOp.var_change_name(tmp_idx_var_name)}]"


@register_tempo_expr_hander("TIMES")
def generate_tempo_expr_times(syntaxExpr, syntaxUserOp, genEqu):
    counter_symbol, counter_name = generate_tmp_symbol_and_register(syntaxUserOp, SyntaxType("int32"), "counter")
    counter_symbol.isOutput = True
    # preCode分为两部分，先根据init决定是否初始化，根据输入的布尔值决定是否自减
    # counter_name需要加入到outC之中
    depth = genEqu.depth
    int_expr = syntaxExpr.objects[0]
    bool_expr = syntaxExpr.objects[1]
    # 根据init初始化
    init_var = syntaxUserOp.set_init_var()
    pre_code = f"{'    ' * depth}kcg_int32 {counter_name};\n"
    pre_code += f"{'    ' * depth}if (outC->{init_var.name}){{\n" \
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
def generate_tempo_expr_when(syntaxExpr, syntaxUserOp, genEqu):
    # when 运算符的目标码为第一个表达式的值，因为 when 运算符在表达式中不改变目标码，仅告知编译器流的时钟即可。
    # 完全没有告知，后面做

    return SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu)


@register_tempo_expr_hander("MERGE")
def generate_tempo_expr_merge(syntaxExpr, syntaxUserOp, genEqu):
    pass


generate_switch_expr_handlers = {}


def register_switch_expr_handler(type_):
    def decorator(func):
        generate_switch_expr_handlers[type_] = func
        return func

    return decorator


@register_switch_expr_handler("IF")
def generate_switch_expr_if(syntaxExpr, syntaxUserOp, genEqu):
    return f"({SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu)} ? {SyntaxExpr_generate(syntaxExpr.objects[1], syntaxUserOp, genEqu)} : {SyntaxExpr_generate(syntaxExpr.objects[2], syntaxUserOp, genEqu)})"


@register_switch_expr_handler("CASE")
def generate_switch_expr_case(syntaxExpr, syntaxUserOp, genEqu):
    tmp_var_symbol, tmp_var_name = generate_tmp_symbol_and_register(syntaxUserOp, syntaxExpr.lhsTypeList[0])
    pre_equations = f"switch({SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu)}){{\n"
    for elem in syntaxExpr.objects[1]:
        syntaxPattern = elem[0]
        syntaxExpr = elem[1]
        if syntaxPattern.value != '_':
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
    return f"({SyntaxExpr_generate(syntax_bool_expr_objects[0], syntaxUserOp, genEqu)}{SyntaxExpr.bool_binary_dict[syntax_bool_expr_objects[1]]}{SyntaxExpr_generate(syntax_bool_expr_objects[2], syntaxUserOp, genEqu)})"


generate_atom_expr_handlers = {}


def register_atom_expr_handler(type_):
    def decorator(func):
        generate_atom_expr_handlers[type_] = func
        return func

    return decorator


@register_atom_expr_handler("bool_atom")
def generate_atom_expr_bool(expr, syntaxUserOp, genEqu):
    return f"kcg_{expr.objects[0]}"


@register_atom_expr_handler("integernum")
def generate_atom_expr_integernum(expr, syntaxUserOp, genEqu):
    _type: SyntaxType = expr.lhsTypeList[0]
    return f"{_type.change_name_cast()}({expr.objects[0]})"


@register_atom_expr_handler("floatnum")
def generate_atom_expr_floatnum(expr, syntaxUserOp, genEqu):
    _type: SyntaxType = expr.lhsTypeList[0]
    return f"{_type.change_name_cast()}({expr.objects[0]})"


@register_atom_expr_handler("character")
def generate_atom_expr_character(expr, syntaxUserOp, genEqu):
    return expr.objects[0]


@register_atom_expr_handler("typed_integer")
def generate_atom_expr_typed_integer(expr, syntaxUserOp, genEqu):
    lst = expr.objects[0].split("_")
    value = lst[0]
    type_str = lst[1].split("i")
    return f"kcg_lit_{'int'.join(type_str)}({value})"


@register_atom_expr_handler("typed_float")
def generate_atom_expr_typed_float(expr, syntaxUserOp, genEqu):
    lst = expr.objects[0].split("_")
    value = lst[0]
    type_str = lst[1][1:]  # 后两位，就是32或者64
    return f"kcg_lit_float{type_str}({value})"


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
    return f"{(syntax_type.change_name_cast())}({SyntaxExpr_generate(expr, syntaxUserOp, genEqu)})"


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
        return f"{SyntaxExpr_generate(syntax_arith_expr_objects[0], syntaxUserOp, genEqu)} {SyntaxExpr.binop_dict[syntax_arith_expr_objects[1]]} {SyntaxExpr_generate(syntax_arith_expr_objects[2], syntaxUserOp, genEqu)}"


generate_id_expr_handlers = {}


def register_id_expr_handler(type_):
    def decorator(func):
        generate_id_expr_handlers[type_] = func
        return func

    return decorator


@register_id_expr_handler("Path_id")
def generate_id_expr_path_id(syntax_id_expr_objects, syntaxUserOp, genEqu):
    path_id = syntax_id_expr_objects[0]  # 获取路径标识符，例如 "n"
    return syntaxUserOp.var_change_name(path_id)


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

    syntaxUserOp.get_my_op_or_state().set_init_var()
    tmp_var, tmp_var_name = generate_tmp_symbol_and_register(syntaxUserOp.get_my_op_or_state(), target_var.syntaxType,
                                                             f"{target_name}_mem_last")
    tmp_var.isOutput = True
    tmp_var.postExpr = f"{syntaxUserOp.var_change_name(tmp_var_name)} = {syntaxUserOp.var_change_name(target_name)};\n"
    tmp_var.lastExpr = target_var.lastExpr
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
        return generate_atom_expr_handler(syntaxExpr, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_Atom_expr , subtype:{subtype_}")


@register_expr_handler('Tempo_expr')
def generate_Tempo_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_tempo_expr_handler = generate_tempo_expr_handlers.get(subtype_)
    if generate_tempo_expr_handler:
        return generate_tempo_expr_handler(syntaxExpr, syntaxUserOp, genEqu)
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
        return generate_switch_expr_handler(syntaxExpr, syntaxUserOp, genEqu)
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


generate_struct_expr_handlers = {}


def register_struct_expr_handler(type_):
    def decorator(func):
        generate_struct_expr_handlers[type_] = func
        return func

    return decorator


@register_expr_handler('Struct_expr')
def generate_Struct_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_struct_expr_handler = generate_struct_expr_handlers.get(subtype_)
    if generate_struct_expr_handler:
        return generate_struct_expr_handler(syntaxExpr, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_struct_expr , subtype:{subtype_}")


@register_struct_expr_handler("get")
def generate_struct_expr_get(syntaxExpr, data_def, genEqu):
    struct = SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)
    return f"{struct}.{syntaxExpr.objects[1]}"


@register_struct_expr_handler("construct")
def generate_struct_expr_construct(syntaxExpr, data_def, genEqu):
    struct_symbol, struct_name = generate_tmp_symbol_and_register(data_def, syntaxExpr.lhsTypeList[0], "struct")
    depth = genEqu.depth
    code = ""
    for pair in syntaxExpr.objects[0]:
        name = pair[0]
        value_expr = pair[1]
        code += assign_lhs_to_rhs_expr(f"{struct_name}.{name}", SyntaxExpr_generate(value_expr, data_def, genEqu),
                                       syntaxExpr.lhsTypeList, depth, data_def)
    genEqu.add_preEquations(code)
    return struct_name


generate_array_expr_handlers = {}


def register_array_expr_handler(type_):
    def decorator(func):
        generate_array_expr_handlers[type_] = func
        return func

    return decorator


@register_expr_handler('Array_expr')
def generate_Array_expr(syntaxExpr, syntaxUserOp, genEqu):
    subtype_ = syntaxExpr.subType
    generate_array_expr_handler = generate_array_expr_handlers.get(subtype_)
    if generate_array_expr_handler:
        return generate_array_expr_handler(syntaxExpr, syntaxUserOp, genEqu)
    else:
        raise ValueError(f"generate_array_expr , subtype:{subtype_}")


@register_array_expr_handler("reverse")
def generate_array_expr_reverse(syntaxExpr, data_def, genEqu):
    array_type: SyntaxType = syntaxExpr.lhsTypeList[0]
    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, array_type)
    idx_symbol, idx_name = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
    depth = genEqu.depth
    src_code = SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)
    pre_code = ""
    pre_code += f"{'    ' * depth}for ({idx_name} = 0; {idx_name} < {array_type.get_size()}; {idx_name}++) {{\n" \
                f"{assign_lhs_to_rhs_expr(f'{tmp_name}[{idx_name}]', f'{src_code}[{array_type.get_size() - 1}-{idx_name}]', [array_type.get_element_type_for_array()], depth + 1, data_def)}" \
                f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    return tmp_name


@register_array_expr_handler("at")
def generate_array_expr_at(syntaxExpr, data_def, genEqu):
    # 列表连接
    array_type: SyntaxType = syntaxExpr.lhsTypeList[0]
    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, array_type)
    depth = genEqu.depth
    tar_first_code = SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)
    tar_second_code = SyntaxExpr_generate(syntaxExpr.objects[1], data_def, genEqu)
    first_size = syntaxExpr.objects[0].lhsTypeList[0].get_size()
    # 把这俩连一起
    pre_code = ""
    pre_code += assign_lhs_to_rhs_expr(tmp_name, tar_first_code, syntaxExpr.objects[0].lhsTypeList, depth, data_def)
    pre_code += assign_lhs_to_rhs_expr(tmp_name + f"[{first_size}]", tar_second_code, syntaxExpr.objects[1].lhsTypeList,
                                       depth, data_def)
    genEqu.add_preEquations(pre_code)
    return tmp_name


@register_array_expr_handler("transpose")
def generate_array_expr_transpose(syntaxExpr, data_def, genEqu):
    src_code = SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)
    dst_symbol, dst_name = generate_tmp_symbol_and_register(data_def, syntaxExpr.lhsTypeList[0])

    src_type = syntaxExpr.objects[0].lhsTypeList[0]
    max_idx = max(syntaxExpr.objects[1], syntaxExpr.objects[2])
    min_idx = min(syntaxExpr.objects[1], syntaxExpr.objects[2])

    depth = genEqu.depth
    idx_names = list()

    # 深度为max的for循环去构建下标
    def generate_pre_code_recursive(cur_depth, cur_type: SyntaxType, idx_count) -> str:
        idx_symbol, idx_name = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
        idx_names.append(idx_name)
        cur_code = ""
        cur_code += f"{'    ' * cur_depth}for ({idx_name} = 0; {idx_name} < {cur_type.get_size()}; {idx_name}++) {{\n"
        if idx_count != max_idx:
            cur_code += f"{generate_pre_code_recursive(cur_depth + 1, cur_type.get_element_type_for_array(), idx_count + 1)}"
        else:
            # 等于max的时候停止递归，输出outC->o3[idx2][idx1][idx] = inC->i3[idx][idx1][idx2];这样的句子来进行具体的操作
            idx_codes = [f"[{idx_name}]" for idx_name in idx_names]
            src = src_code + "".join(idx_codes)
            idx_codes[min_idx - 1], idx_codes[max_idx - 1] = idx_codes[max_idx - 1], idx_codes[min_idx - 1]
            dst = dst_name + "".join(idx_codes)
            cur_code += assign_lhs_to_rhs_expr(dst, src, [cur_type], cur_depth, data_def)
        cur_code += f"{'    ' * cur_depth}}}\n"
        return cur_code

    pre_code = generate_pre_code_recursive(depth, src_type, 1)
    genEqu.add_preEquations(pre_code)
    return dst_name


@register_array_expr_handler("construct")
def generate_array_expr_construct(syntaxExpr, data_def, genEqu):
    tmp_para, tmp_name = generate_tmp_symbol_and_register(data_def, syntaxExpr.lhsTypeList[0], "array_tmp")
    size = cal_const_expr(syntaxExpr.objects[1], SyntaxType("integer"), data_def).value
    element = SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)
    code = f"{'    ' * genEqu.depth}for(kcg_size idx{genEqu.depth}=0;idx{genEqu.depth}<{size};idx{genEqu.depth}++){{\n" \
           f"{'    ' * (genEqu.depth + 1)}{tmp_name}[idx{genEqu.depth}] = {element};\n" \
           f"{'    ' * genEqu.depth}}}\n"
    genEqu.add_preEquations(code)
    return tmp_name


@register_array_expr_handler("list")
def generate_array_expr_list(syntaxExpr, data_def, genEqu):
    # 数组初始化函数，直接写成{a,b,c,d}即可
    elements: list[SyntaxExpr] = syntaxExpr.objects[0].objects[0]
    return f"{{{', '.join([SyntaxExpr_generate(expr, data_def, genEqu) for expr in elements])}}}"


@register_array_expr_handler("get")
def generate_array_expr_get(syntaxExpr, data_def, genEqu):
    idx = syntaxExpr.idx_list[0]
    return f"{SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)}[{idx}]"


@register_array_expr_handler("getdefault")
def generate_array_expr_getdefault(syntaxExpr, data_def, genEqu: GenEqu):
    # 要在这里检查idx是不是超过数组长度了
    # 可以get很多层，所以需要递归的看数组
    depth = genEqu.depth
    tmp_var, tmp_name = generate_tmp_symbol_and_register(data_def, syntaxExpr.lhsTypeList[0])

    normal_expr: SyntaxExpr = syntaxExpr.objects[0]
    normal_code = SyntaxExpr_generate(normal_expr, data_def, genEqu)
    arr_type = normal_expr.lhsTypeList[0]
    cur_type = arr_type
    cmp_code_list = []
    for idx_expr in syntaxExpr.objects[1]:
        idx_code = SyntaxExpr_generate(idx_expr, data_def, genEqu)
        normal_code += f"[{idx_code}]"
        # 构建校验是否超出数组上限的表达式
        cur_size = cur_type.get_size()
        cur_type = cur_type.arrayType
        cmp_code_list.append(f"((kcg_lit_int32(0) <= {idx_code})&({idx_code} < kcg_lit_int32({cur_size})))")
    cmp_code = '&'.join(cmp_code_list)

    get_normal_code = assign_lhs_to_rhs_expr(tmp_name, normal_code, syntaxExpr.lhsTypeList, depth + 1, data_def)

    default_expr: SyntaxExpr = syntaxExpr.objects[2]
    default_code = SyntaxExpr_generate(default_expr, data_def, genEqu)
    get_default_code = assign_lhs_to_rhs_expr(tmp_name, default_code, syntaxExpr.lhsTypeList, depth + 1, data_def)

    pre_code = f"{'    ' * depth}if({cmp_code}){{\n" \
               f"{get_normal_code}" \
               f"{'    ' * depth}}}\n" \
               f"{'    ' * depth}else {{\n" \
               f"{get_default_code}" \
               f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    return tmp_name


@register_array_expr_handler("slice")
def generate_array_expr_slice(syntaxExpr: SyntaxExpr, data_def, genEqu: GenEqu):
    depth = genEqu.depth
    tmp_var, tmp_name = generate_tmp_symbol_and_register(data_def, syntaxExpr.lhsTypeList[0])
    sliced_code = SyntaxExpr_generate(syntaxExpr.objects[0], data_def, genEqu)
    slice_type_name = syntaxExpr.lhsTypeList[0].change_name()

    genEqu.add_preEquations(
        f"{'    ' * depth}kcg_assign_array(&({tmp_name}),  ({slice_type_name} *) &(({sliced_code})[{syntaxExpr.idx_list[0]}]), sizeof ({slice_type_name}));\n")
    return tmp_name


@register_expr_handler('Apply_expr')
def generate_Apply_expr(syntaxExpr, syntaxUserOp, genEqu):
    # 对函数调用情况的代码生成
    # 在文档里给出了详细的描述
    # 先生成operator对应的代码，若函数调用情况则会对结构体进行修改，若make和flatten则直接返回一个对象
    operator = syntaxExpr.objects[0]
    parameters = syntaxExpr.objects[1].objects[0]
    if syntaxExpr.appliedOp is not None and syntaxExpr.appliedOp.hasInternalState:
        # 如果调用了函数，且函数有内存，就要构造outc并进行传递

        generate_and_register_outC_name(syntaxUserOp.get_my_userOp(), syntaxExpr.appliedOp, syntaxExpr)
        applied_outc_name = f"outC->{syntaxExpr.appliedOpOutCName}"
    else:
        applied_outc_name = None
    # todo 下面的代码要修改一下，要求把参数表达式拆分成多个单返回值的表达式，这样进行operator处理时候会方便很多
    # for param in parameters:
    #     param_lhs_symbols=[]
    #     param_lhs_names=[]
    #     for param_lhs in param.lhsTypeList:
    #         lhs_symbol,lhs_name=generate_tmp_symbol_and_register(data_def,param_lhs,"fold_param")
    #         param_lhs_symbols.append(lhs_symbol)
    #         param_lhs_names.append(lhs_name)
    #     equivalent_equation=SyntaxEquation(type="simple_equation",lhs=param_lhs_names)
    #     equivalent_equation.set_expr(param)
    #     sub_param_code+=generate_userOp_simple_equation(equivalent_equation,data_def,None,depth+1)
    return generate_operator(operator, parameters, syntaxUserOp, genEqu, applied_outc_name)


generate_operator_handlers = {}


def register_operator_handler(type_):
    def decorator(func):
        generate_operator_handlers[type_] = func
        return func

    return decorator


def generate_operator(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope, genEqu,
                      applied_outc_name):
    subtype_ = operator.subtype
    generate_operator_handler = generate_operator_handlers.get(subtype_)
    if generate_operator_handler:
        return generate_operator_handler(operator, parameters, data_def, genEqu, applied_outc_name)
    else:
        raise ValueError(f"generate_operator , subtype:{subtype_}")


generate_operator_iterator_handlers = {}


def register_operator_iterator_handler(type_):
    def decorator(func):
        generate_operator_iterator_handlers[type_] = func
        return func

    return decorator


@register_operator_handler("iterator")
def generate_operator_iterator(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                               genEqu, applied_outc_name):
    # 根据不同的算符，组建新的参数表达式交给下级operator
    operator_name = operator.objects[0].replace('i', "")  # "map"等
    iterator_handler = generate_operator_iterator_handlers.get(operator_name)
    if iterator_handler is None:
        raise Exception(f"iterator之{operator_name}没有实现代码生成")
    return iterator_handler(operator, parameters, data_def, genEqu, applied_outc_name, 'i' in operator.objects[0])


def generate_tmp_symbol_and_register(data_def, syntaxType: SyntaxType = None, post_fix="tmp") -> (
SyntaxVariableSymbol, str):
    tmp_name = data_def.generate_name_for_tmp(post_fix)
    tmp_symbol = SyntaxVariableSymbol(tmp_name, False, False, data_def)
    tmp_symbol.syntaxType = syntaxType
    data_def.add_tmpSymbol(tmp_symbol)
    return tmp_symbol, tmp_name


def symbol2expr(symbol, symbol_name, symbol_type, scope):
    expr = SyntaxExpr(type="Id_expr", subtype="Path_id", scope=scope, objects=[symbol_name])
    expr.set_symbol(symbol)
    expr.set_lhs_type([symbol_type])
    return expr


def assign_lhs_to_rhs_expr(lhs_symbol_name: str or list[str], rhs_expr: str or list[str], type_list: list[SyntaxType],
                           depth, data_def):
    code = ""
    # 很蠢的方法，后面一定会改
    # 现在变成了一般蠢的方法，后面也不一定会改
    if not isinstance(lhs_symbol_name, list):
        lhs_names = [lhs_symbol_name]
    else:
        lhs_names = lhs_symbol_name
    if not isinstance(rhs_expr, list):
        rhs_exprs = [rhs_expr]
    else:
        rhs_exprs = rhs_expr

    if len(rhs_exprs) != len(lhs_names) or len(lhs_names) != len(type_list):
        raise Exception(f"不对，左值{lhs_names}和右值{rhs_exprs}以及类型列表{type_list}对不上")
    for lhs, rhs, lhsType in zip(lhs_names, rhs_exprs, type_list):
        if lhs == "_": continue
        if lhsType.type == "array":
            code += f"{'    ' * depth}memcpy(&{lhs},&({rhs}),sizeof({lhsType.change_name()}));\n"
        else:
            code += f"{'    ' * depth}{lhs} = {rhs};\n"
    return code


def get_element_for_parameters(parameters: list[SyntaxExpr], data_def, depth, idx_name, tmp_post_fix="tmp") -> (
str, list[SyntaxExpr]):
    """返回一个precode和新参数表达式列表"""
    sub_parameters = list()
    genEqu = GenEqu(depth)
    for parameter in parameters:
        para_type = parameter.lhsTypeList[0]
        tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, para_type.get_element_type_for_array(),
                                                                tmp_post_fix)
        para_code = SyntaxExpr_generate(parameter, data_def, genEqu)
        pre_code = assign_lhs_to_rhs_expr(tmp_name, para_code + f"[{idx_name}]", [para_type], genEqu.depth, data_def)
        genEqu.add_preEquations(pre_code)
        sub_parameters.append(symbol2expr(tmp_symbol, tmp_name, para_type, data_def))
    return "".join(genEqu.preEquations), sub_parameters


@register_operator_iterator_handler("fold")
def generate_iterator_fold(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                           genEqu: GenEqu, applied_outc_name, hasI: bool):
    depth = genEqu.depth
    array_length = operator.array_length
    # 先生成一个临时变量遍历数组
    tmp_idx_symbol, tmp_idx = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
    # 然后是一个临时变量用来接住次级operator的返回值
    tmp_output_symbol, tmp_output_name = generate_tmp_symbol_and_register(data_def, operator.lhsTypeList[0],
                                                                          post_fix="fold_out")
    # 然后是为所有参数都生成一个变量用来向下传递
    sub_params = []
    if hasI:
        sub_params.append(symbol2expr(tmp_idx_symbol, tmp_idx, tmp_idx_symbol.syntaxType, data_def))
    sub_param_code = ""
    for i in range(len(parameters)):
        param = parameters[i]
        base_type = param.lhsTypeList[0]
        param_code = SyntaxExpr_generate(param, data_def, genEqu)
        if i == 0:
            sub_symbol, sub_name = generate_tmp_symbol_and_register(data_def, base_type, f"fold_{i + 1}")
            sub_param_code += f"{'    ' * (depth + 1)}{sub_name} = {tmp_idx}==0?{param_code}:{tmp_output_name};\n"
            # 进行初始化操作
        else:
            base_type = base_type.get_element_type_for_array()
            sub_symbol, sub_name = generate_tmp_symbol_and_register(data_def, base_type, f"fold_{i + 1}")
            sub_param_code += f"{'    ' * (depth + 1)}{sub_name} = {param_code}[{tmp_idx}];\n"
            # 进行取值操作
        sub_params.append(symbol2expr(sub_symbol, sub_name, base_type, data_def))
    # 然后构建最终产生的代码
    sub_gen_equ = GenEqu(depth=depth + 1)
    sub_operator = operator.objects[2]
    sub_gen_equ.expr = generate_operator(sub_operator, sub_params, data_def, sub_gen_equ,
                                         f"{applied_outc_name}[{tmp_idx}]")
    pre_code = f"{'    ' * depth}for ({tmp_idx} = 0; {tmp_idx} < {str(array_length)}; {tmp_idx}++) {{\n" \
               f"{sub_param_code}" \
               f"{''.join(sub_gen_equ.preEquations)}" \
               f"{'    ' * (depth + 1)}{tmp_output_name}={sub_gen_equ.expr};\n" \
               f"{'    ' * depth}}}\n"
    # fold只返回一个变量，直接用=赋值是安全的
    genEqu.add_preEquations(pre_code)
    return tmp_output_name


@register_operator_handler("foldw")
def generate_operator_foldw(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                            genEqu: GenEqu, applied_outc_name, hasI: bool):
    # 返回两个变量，第一个为idx，即实际循环执行次数
    # 第二个为acc，为累加器
    # 参数输入为一个累加器，和剩下的普通数组迭代
    depth = genEqu.depth
    return_types = operator.lhsTypeList
    idx_out_symbol, idx_out_name = generate_tmp_symbol_and_register(data_def, return_types[0], "idx_out")
    idx_symbol, idx_name = generate_tmp_symbol_and_register(data_def, return_types[0], "idx")  # for循环中的idx
    acc_symbol, acc_name = generate_tmp_symbol_and_register(data_def, return_types[1], "acc")
    cond_iterw_symbol, cond_iterw_name = generate_tmp_symbol_and_register(data_def, SyntaxType("bool"), "cond_iterw")

    # 内部op的返回一个bool的cond_iterw和一个acc
    # acc既是第一个输入参数，也是第二个输出参数
    # 然后cond_iterw是第一个输出参数
    # 其他的输入参数从parameter中构建
    # 下面是一个差不多的示例，确实有点看不懂（
    """
      acc = inC->i1;
  if (inC->cond) {
    for (idx = 0; idx < 3; idx++) {
      foldw_in(acc, inC->i2[idx], &cond_iterw, &acc);
      outC->o1 = (kcg_int32) (idx + 1);
      if (!cond_iterw) {
        break;
      }
    }
  }
  else {
    outC->o1 = kcg_lit_int32(0);
  }
    """
    sub_parameters = [symbol2expr(acc_symbol, acc_name, return_types[1], data_def)]
    sub_pre_code, sub_element_codes = get_element_for_parameters(parameters[1:], data_def, depth + 1, idx_name, "foldw")
    sub_parameters.extend(sub_element_codes)
    sub_genEqu = GenEqu(depth + 1)
    sub_operator_code = generate_operator(operator.objects[0], sub_parameters, data_def, sub_genEqu, applied_outc_name)
    pre_code = ""
    pre_code += assign_lhs_to_rhs_expr(acc_name, SyntaxExpr_generate(parameters[0], data_def, genEqu),
                                       parameters[0].lhsTypeList, depth, data_def)
    pre_code += f"{'    ' * depth}if ({SyntaxExpr_generate(operator.objects[2], data_def, genEqu)}){{\n" \
                f"{'    ' * (depth + 1)}for ({idx_name} = 0; {idx_name} < {cal_const_expr(operator.objects[1], SyntaxType('integer'), data_def).value}; {idx_name}++){{\n" \
                f"{sub_pre_code}" \
                f"{''.join(sub_genEqu.preEquations)}" \
                f"{assign_lhs_to_rhs_expr([cond_iterw_name, acc_name], sub_operator_code, [SyntaxType('bool'), return_types[1]], depth + 1, data_def)}" \
                f"{'    ' * (depth + 1)}{idx_out_name} = (kcg_int32) ({idx_name} + 1);" \
                f"{'    ' * (depth + 1)}if (!{cond_iterw_name}) {{break}};\n" \
                f"{'    ' * (depth + 1)}}}\n" \
                f"{'    ' * depth}}}\n" \
                f"{'    ' * depth}else {{\n" \
                f"{'    ' * depth}{idx_out_name} = kcg_lit_int32(0);" \
                f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    return [idx_out_name, acc_name]


@register_operator_iterator_handler("mapfold")
def generate_iterator_mapfold(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                              genEqu,
                              applied_outc_name, hasI: bool):
    depth = genEqu.depth
    map_idx = operator.objects[1]
    # 先生成一个临时变量遍历数组
    tmp_idx_symbol, tmp_idx = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
    pre_code = ""
    fold_symbols = list()
    # 给属于fold的变量赋初始值
    for i in range(map_idx):
        # 这边都是fold
        fold_symbol, fold_name = generate_tmp_symbol_and_register(data_def, operator.lhsTypeList[i], "fold")
        fold_symbols.append(fold_symbol)
        pre_code += assign_lhs_to_rhs_expr(fold_symbol, SyntaxExpr_generate(parameters[i], data_def, genEqu),
                                           [operator.lhsTypeList[i]], depth, data_def)
    # map变量的声明和赋值操作
    # 这些都是输入变量
    map_pre_codes, sub_params_map = get_element_for_parameters(parameters[map_idx:], data_def, depth + 1, tmp_idx,
                                                               "map")
    sub_params = [symbol2expr(symbol, symbol.name, symbol.syntaxType, data_def) for symbol in
                  fold_symbols] + sub_params_map
    sub_genEqu = GenEqu(depth + 1)
    sub_operator_code = generate_operator(operator.objects[1], sub_params, data_def, sub_genEqu, applied_outc_name)
    # 上面就完成了所有子operator的构造过程
    # 下面要把子operator的输出和对应的输入匹配起来
    map_out_symbols = list()
    for i in (map_idx, len(operator.lhsTypeList) + 1):
        map_out_symbol, map_out_name = generate_tmp_symbol_and_register(data_def, operator.lhsTypeList[i], "map_out")
        map_out_symbols.append(map_out_symbol)
    # 构建赋值的左值名字列表
    # 和子operator的返回值一一对应
    lhs_types = operator.lhsTypeList
    lhs_types = [lhs_types[i] if i < map_idx else lhs_types[i].get_element_type_for_array() for i in
                 range(len(lhs_types))]
    lhs_codes = [symbol.name for symbol in fold_symbols] + [symbol.name + f"[{tmp_idx}]" for symbol in map_out_symbols]
    post_assign_code = assign_lhs_to_rhs_expr(lhs_codes, sub_operator_code, lhs_types,depth+1,data_def)

    # 进行for循环
    pre_code += f"{'    ' * depth}for ({tmp_idx} = 0; {tmp_idx} < {cal_const_expr(operator.objects[3], SyntaxType('int32'), data_def).value}; {tmp_idx}++) {{\n" \
                f"{map_pre_codes}" \
                f"{''.join(sub_genEqu.preEquations)}" \
                f"{post_assign_code}"
    pre_code += f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    out_symbols=fold_symbols+map_out_symbols
    return [symbol.name for symbol in out_symbols]


@register_operator_iterator_handler("map")
def generate_iterator_map(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope, genEqu,
                          applied_outc_name, hasI: bool):
    # map可以多返回值，此处应该返回结构体
    # 但是我做出了一个违背祖宗的决定，返回一个表达式列表，在simple_equation那里挨个进行赋值
    depth = genEqu.depth
    array_length = operator.array_length
    # 先生成一个临时变量遍历数组
    tmp_idx_symbol, tmp_idx = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
    # 然后是一些临时变量用来接住次级operator的返回值
    tmp_output_names = []

    for lhs in operator.lhsTypeList:
        tmp_output_symbol, tmp_output_name = generate_tmp_symbol_and_register(data_def, lhs, post_fix="map_out")
        tmp_output_names.append(tmp_output_name)
    # 然后构建传给次级operator的参数
    sub_param_code = ""
    sub_params = []
    if hasI:
        sub_params.append(symbol2expr(tmp_idx_symbol, tmp_idx, tmp_idx_symbol.syntaxType, data_def))
    for i in range(len(parameters)):
        param = parameters[i]
        param_code = SyntaxExpr_generate(param, data_def, genEqu)
        base_type = param.lhsTypeList[0].get_element_type_for_array()
        sub_symbol, sub_name = generate_tmp_symbol_and_register(data_def, base_type, f"map_{i + 1}")
        sub_param_code += f"{'    ' * (depth + 1)}{sub_name} = {param_code}[{tmp_idx}];\n"
        sub_params.append(symbol2expr(sub_symbol, sub_name, base_type, data_def))
    # 然后构建最终产生的代码
    sub_gen_equ = GenEqu(depth=depth + 1)
    sub_operator = operator.objects[2]
    sub_gen_equ.expr = generate_operator(sub_operator, sub_params, data_def, sub_gen_equ,
                                         f"{applied_outc_name}[{tmp_idx}]")
    pre_code = f"{'    ' * depth}for ({tmp_idx} = 0; {tmp_idx} < {str(array_length)}; {tmp_idx}++) {{\n" \
               f"{sub_param_code}" \
               f"{''.join(sub_gen_equ.preEquations)}" \
               f"{assign_lhs_to_rhs_expr([f'{name}[{tmp_idx}]' for name in tmp_output_names], sub_gen_equ.expr, operator.lhsTypeList, depth + 1, data_def)}" \
               f"{'    ' * depth}}}\n"

    genEqu.add_preEquations(pre_code)
    return tmp_output_names


def generate_and_register_inC(data_def, applied_userOp):
    """生成一个inc对象并注册,inc肯定是一个临时变量"""
    inc_type = SyntaxType("other")
    inc_type.value = applied_userOp.get_inC_name()
    inc_symbol, inc_name = generate_tmp_symbol_and_register(data_def, inc_type,
                                                            applied_userOp.get_global_name() + "_inC")
    return inc_name


def generate_and_register_outC_name(userOp: SyntaxUserOp, applied_userOp, expr: SyntaxExpr):
    name = userOp.register_outC_name(applied_userOp.get_outC_name())
    expr.appliedOpOutCName = name
    return name


def generate_and_register_outC(data_def, applied_userOp):
    # 没内存，就要自己生成一个临时变量outC
    outc_type = SyntaxType("other")
    outc_type.value = applied_userOp.get_outC_name()
    outc_symbol, outC_name = generate_tmp_symbol_and_register(data_def, outc_type,
                                                              applied_userOp.get_global_name() + "_outC")
    return outC_name


@register_operator_handler("activateDefault")
def generate_operator_activateDefault(operator: SyntaxOperator, parameters: list[SyntaxExpr],
                                      data_def: SyntaxDataDefScope,
                                      genEqu: GenEqu, applied_outc_name):
    depth = genEqu.depth
    cond_code = SyntaxExpr_generate(operator.objects[1], data_def, genEqu)
    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, operator.lhsTypeList[0])
    default_code = assign_lhs_to_rhs_expr(tmp_name, SyntaxExpr_generate(operator.objects[2], data_def, genEqu)
                                          , operator.lhsTypeList, depth, data_def)
    activate_code = assign_lhs_to_rhs_expr(tmp_name,
                                           generate_operator(operator.objects[0], parameters, data_def, genEqu,
                                                             applied_outc_name),
                                           operator.lhsTypeList, depth, data_def)
    pre_code = f"{'    ' * depth}if({cond_code}){{\n" \
               f"{activate_code}" \
               f"{'    ' * depth}}}\n" \
               f"{'    ' * depth}else {{\n" \
               f"{default_code}" \
               f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    return tmp_name


@register_operator_handler("activateInitDefault")
def generate_operator_activateInitDefault(operator: SyntaxOperator, parameters: list[SyntaxExpr],
                                          data_def: SyntaxDataDefScope,
                                          genEqu: GenEqu, applied_outc_name):
    depth = genEqu.depth
    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, operator.lhsTypeList[0])
    tmp_symbol.isOutput = True
    init_var: SyntaxVariableSymbol = data_def.set_init_var()

    cond_code = SyntaxExpr_generate(operator.objects[1], data_def, genEqu)
    activate_code = assign_lhs_to_rhs_expr(data_def.var_change_name(tmp_symbol.name),
                                           generate_operator(operator.objects[0], parameters, data_def, genEqu,
                                                             applied_outc_name),
                                           operator.lhsTypeList, depth, data_def)
    init_code = assign_lhs_to_rhs_expr(data_def.var_change_name(tmp_symbol.name),
                                       SyntaxExpr_generate(operator.objects[2], data_def, genEqu)
                                       , operator.lhsTypeList, depth, data_def)
    pre_code = f"{'    ' * depth}if({cond_code}){{\n" \
               f"{activate_code}" \
               f"{'    ' * depth}}}\n" \
               f"{'    ' * depth}else if({data_def.var_change_name(init_var.name)}){{\n" \
               f"{init_code}" \
               f"{'    ' * depth}}}\n"
    genEqu.add_preEquations(pre_code)
    return data_def.var_change_name(tmp_name)


@register_operator_handler("make")
def generate_operator_make(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                           genEqu: GenEqu, applied_outc_name):
    # 搓指定结构体
    tar_type = operator.lhsTypeList[0].get_real_type()
    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, tar_type)

    # 竟如此简洁，太棒了
    param_codes = [SyntaxExpr_generate(expr, data_def, genEqu) for expr in parameters]
    lhs_names = [f"{tmp_name}.{field.name}" for field in tar_type.fields]
    types = [field.syntaxType for field in tar_type.fields]
    pre_code = assign_lhs_to_rhs_expr(lhs_names, param_codes, types, genEqu.depth, data_def)
    genEqu.add_preEquations(pre_code)
    return tmp_name


@register_operator_handler("flatten")
def generate_operator_flatten(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                              genEqu: GenEqu, applied_outc_name):
    # 展开指定结构体,这下要返回多个str了

    tar_expr = parameters[0]
    tar_type = tar_expr.lhsTypeList[0].get_real_type()
    if tar_expr.type != "Id_expr":
        tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def, tar_type)
        genEqu.add_preEquations(assign_lhs_to_rhs_expr(tmp_name, SyntaxExpr_generate(parameters[0], data_def, genEqu),
                                                       operator.lhsTypeList, genEqu.depth, data_def))
        tar_struct_name = tmp_name
    else:
        tar_struct_name = SyntaxExpr_generate(tar_expr, data_def, genEqu)

    fields = tar_type.fields
    out_cods = [f"{tar_struct_name}.{field.name}" for field in fields]
    return out_cods


@register_operator_handler("Path_id")
def generate_operator_Path_id(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                              genEqu, applied_outc_name):
    # 这里是函数调用语句
    # 生成一个inC结构体，将输入参数填入
    # 生成一个空outC结构体
    # 如果是node，则这个outC去当前函数的outC里面取
    # 如果是function，就直接初始化一个，说实话有点恶心
    # 结束调用后，把outC里面的结果拿出来进行进一步赋值操作

    applied_userOp = operator.appliedUserOp
    global_name = applied_userOp.get_global_name()
    if applied_userOp.isImported:
        # 拿一下输入参数对应代码
        param_code = ", ".join(SyntaxExpr_generate(param, data_def, genEqu) for param in parameters)
        applied_code = GenerateCode.generate_imported_function_name(applied_userOp)
        applied_code += f"({param_code})"
        return applied_code

    code = ""
    # inC需要自己进行构造，outC可能出现在此函数的outC中
    tmp_inC_name = generate_and_register_inC(data_def, applied_userOp)
    if applied_userOp.hasInternalState:
        tmp_outC_name = applied_outc_name
    else:
        tmp_outC_name = generate_and_register_outC(data_def, applied_userOp)

    # 填充inc结构体
    for idx, param in enumerate(parameters):
        param_code = SyntaxExpr_generate(param, data_def, genEqu)
        in_param = applied_userOp.inParams[idx]
        code += assign_lhs_to_rhs_expr(f"{tmp_inC_name}.{in_param.name}", param_code, [in_param.syntaxType],
                                       genEqu.depth, data_def)

    # 进行函数调用
    code += f"{'    ' * genEqu.depth}{global_name}(&{tmp_inC_name}, &{tmp_outC_name});\n"

    # 把outC中的结果取出
    output_names = []
    for out_param in applied_userOp.outParams:
        output_name = f"{tmp_outC_name}.{out_param.name}"
        output_names.append(output_name)

    # 添加代码到preEquations中
    genEqu.add_preEquations(code)
    return output_names if len(output_names) > 1 else output_names[0]


@register_operator_handler("PREFIXOP")
def generate_operator_PREFIXOP(operator: SyntaxOperator, parameters: list[SyntaxExpr], data_def: SyntaxDataDefScope,
                               genEqu, applied_outc_name):
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
        equivalent_expr.add_object(parameters[0])
    else:
        equivalent_expr.add_object(parameters[0])
        if prefixOp != "$@$" and prefixOp != "$times$":
            equivalent_expr.add_object(prefixOp.replace("$", ""))
        equivalent_expr.add_object(parameters[1])
    return SyntaxExpr_generate(equivalent_expr, data_def, genEqu)


@register_expr_handler('Mixed_constructor')
def generate_Mixed_constructor(syntaxExpr, syntaxUserOp, genEqu):
    # 先copy，然后修改
    struct_type = syntaxExpr.lhsTypeList[0]
    tmp_symbol, tmp_name = generate_tmp_symbol_and_register(syntaxUserOp, struct_type, "struct")

    depth = genEqu.depth

    pre_code = ""
    pre_code += assign_lhs_to_rhs_expr(tmp_name, SyntaxExpr_generate(syntaxExpr.objects[0], syntaxUserOp, genEqu),
                                       syntaxExpr.lhsTypeList, depth, syntaxUserOp)
    lhs_name = tmp_name
    for idx in syntaxExpr.objects[1]:
        # 拼一下下标和取数部分
        if isinstance(idx, str):
            lhs_name += "." + idx
        elif isinstance(idx, SyntaxExpr):
            lhs_name += f"[{cal_const_expr(idx, SyntaxType('integer'), syntaxUserOp).value}]"
    pre_code += assign_lhs_to_rhs_expr(lhs_name, SyntaxExpr_generate(syntaxExpr.objects[2], syntaxUserOp, genEqu),
                                       syntaxExpr.objects[2].lhsTypeList, depth, syntaxUserOp)
    genEqu.add_preEquations(pre_code)
    return tmp_name


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
    # if syntaxEquation.lhs[0] == "_": return ""
    # lhs_symbol = syntaxUserOp.get_localVariable_InThisAndPreEnv(syntaxEquation.lhs[0])
    # if lhs_symbol is None: lhs_symbol = syntaxUserOp.get_tmpSymbol(syntaxEquation.lhs[0])

    lhs_types = []
    for lhs in syntaxEquation.lhs:
        if lhs == "_":
            lhs_types.append(SyntaxType("any"))
        else:
            lhs_symbol = syntaxUserOp.get_localVariable_InThisAndPreEnv(lhs)
            lhs_types.append(lhs_symbol.syntaxType)
    genEqu = GenEqu(depth)
    genEqu.expr = SyntaxExpr_generate(syntaxEquation.expr, syntaxUserOp, genEqu)
    code = ""
    code += "".join(genEqu.preEquations)
    code += assign_lhs_to_rhs_expr([syntaxUserOp.var_change_name(lhs) for lhs in syntaxEquation.lhs], genEqu.expr,
                                   lhs_types, depth, syntaxUserOp)
    # code += f"{'    ' * depth}{syntaxUserOp.var_change_name(syntaxEquation.lhs[0])} = {genEqu.expr};\n"
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
        code += f"{'    ' * depth}{signal} = kcg_true;\n"
    return code


@register_userOp_handler("control_block")
def generate_userOp_control_block(syntaxEquation, syntaxUserOp, code_generator, depth=1):
    control_block_ID = syntaxEquation.controlBlockID
    control_block = syntaxUserOp.get_childScope(control_block_ID)
    if control_block is None: raise UnknownIdentifierException(f"control_block {control_block_ID} 没有找到")
    # print("this is control_block", syntaxEquation.controlBlockID)
    if control_block.type == "automaton":
        return generate_automaton(control_block, code_generator, depth)
    if control_block.type == "if_block":
        if_block = control_block.block
        return generate_if_block(if_block, code_generator, depth)


def generate_automaton(control_block, code_generator, depth) -> str:
    code_generator.add_code_to_types_file(automaton_generate.generate_type(control_block))
    # print("HEAD:")
    # print(automaton_generate.generate_state_nxt_for_head(control_block))
    # print("INIT:")
    # print(automaton_generate.generate_init_symbol_for_init(control_block))
    return automaton_generate.generate_body(control_block, code_generator, depth)


def generate_if_block(block: SyntaxIfBlock, code_generator, depth) -> str:
    scope = block.scope
    condition_genEqu = GenEqu(depth)
    condition_genEqu.expr = SyntaxExpr_generate(block.conditionExpr, scope, GenEqu(depth))

    def generate_if_sub_block(sub_block: str or SyntaxIfBlock) -> str:
        if isinstance(sub_block, str):
            sub_data_def: SyntaxDataDefScope = scope.get_childScope(sub_block)
            return code_generator.generate_data_def(sub_data_def, depth + 1)
        else:
            return generate_if_block(sub_block, code_generator, depth + 1)

    then_code = generate_if_sub_block(block.thenBlock)
    else_code = generate_if_sub_block(block.elseBlock)

    code = f"{'    ' * depth}{''.join(condition_genEqu.preEquations)}\n" if condition_genEqu.preEquations else ""
    code += f"{'    ' * depth}if ({condition_genEqu.expr}){{\n"
    code += then_code
    code += f"{'    ' * depth}}}\n"
    code += f"{'    ' * depth}else{{\n"
    code += else_code
    code += f"{'    ' * depth}}}\n"
    return code


def SyntaxUserOp_generate(syntaxUserOp, code_generator, depth):
    code = ""
    for elem in syntaxUserOp.equations:
        try:
            type_ = elem.type
            generate_userOp_handler = generate_userOp_handlers.get(type_)
            if generate_userOp_handler:
                code += generate_userOp_handler(elem, syntaxUserOp, code_generator, depth)
            else:
                raise ValueError(f"syntaxUserOp_generate error , type : {type_}")
        except Exception as e:
            print(f"发生错误的句子:{elem},在{syntaxUserOp.get_global_name()}内", file=sys.stdout)
            raise e
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
    var_name = f"{typeSymbol.name}_{global_name}"
    code = f"typedef enum {var_name} {{\n"
    for idx, enum_symbol in enumerate(typeSymbol.syntaxType.enumList):
        if idx != 0:
            code += ",\n"
        code += f"{enum_symbol.name}_{global_name}"
    code += f"\n}} {var_name};\n"
    print("=== enum ===")
    print(code)
    # 不对啊不对
    # 具体哪不对你怎么不告诉我??
    return code


@register_syntax_type_handler(r"^field_decl")
def generate_syntax_type_field_decl(typeSymbol, rootPackage):
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.syntaxType.change_name()
    precode = ""
    code = f"typedef struct {var_name} {{\n"
    for field in typeSymbol.syntaxType.fields:
        k = field.name
        v = field.syntaxType
        if v.get_real_type() in v.basic_type:
            code += f"kcg_{v.type} {k};\n"
        else:
            tmpTypeSymbol = SyntaxTypeSymbol(f"tmp_struct_{k}", v.get_real_type(), "public")
            precode = generate_type_symbol(tmpTypeSymbol, rootPackage)
            tmpName = f"tmp_struct_{k}" if len(global_name) == 0 else f"tmp_struct_{k}_{global_name}"
            code += f"{tmpName} {k};\n"
    code += f"\n}} {var_name};\n"
    code = precode + code
    return code


def generate_syntax_type_list_recursive(syntaxType, rootPackage, symbolName):
    if syntaxType.type == "array":
        type_, code_ = generate_syntax_type_list_recursive(syntaxType.get_element_type_for_array(), rootPackage,
                                                           symbolName)
        size_ = syntaxType.get_size()
        name_ = f"{symbolName}_array_{size_}"
        code_ += f"typedef {type_} {name_}[{size_}];\n"
        return name_, code_
    else:
        code_ = syntaxType.change_name()
        return code_, ""


@register_syntax_type_handler(r"^array")
def generate_syntax_type_list(typeSymbol, rootPackage):
    print("this is array ", typeSymbol.name, typeSymbol.syntaxType.get_size(),
          typeSymbol.syntaxType.get_element_type_for_array())
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
        if not constSymbol.used: continue
        if constSymbol.syntaxType.get_real_type().type == "enum": continue
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
            c_content += f"const {symbol_type} {symbol_name}={SyntaxExpr_generate(constSymbol.valueExpr, rootPackage, GenEqu())};\n"
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


def scade_parse(input_path: str, main_operator: str, output_path: str, need_test_file: bool):
    parser = yacc(debug=1, start="Program")

    file = open(input_path, 'r')
    strs = file.read()
    file.close()

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

    userOp_order = post_process(root_scope, main_operator)
    print("最终进行代码生成的op:")
    print([op for op in userOp_order])
    print("有最终的遍历顺序为:")
    print([op.get_global_name() for op in userOp_order])
    # 后处理流程，在这里进行拓扑排序，类型校验，模板函数实例化等问题，会对语法树进行更新

    gen = GenerateCode(root_scope, main_operator, output_path)
    gen.generate_const_file()
    # gen.generate_main_file()
    gen.generate_types_file()

    for op in userOp_order:
        gen.generate_node_file(op)
    gen.generate_imported_functions_file()
    gen.add_code_to_types_file("#endif\n")  # 结束
    if need_test_file:
        print(f"生成测试类:{userOp_order[-1].name}")
        gen.generate_test_file(userOp_order[-1])


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-m', '--main_operator', required=True, type=str)
    argParser.add_argument('-o', '--output_path', required=True, type=str)
    argParser.add_argument('-t', '--need_test_file', required=False, type=bool, default=False)
    args = argParser.parse_args()
    scade_parse(args.input_path, args.main_operator, args.output_path, args.need_test_file)
