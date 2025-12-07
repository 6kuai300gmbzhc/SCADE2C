import os.path
import re
import sys
from collections import deque

from syntax_tree.syntax_class.Exceptions import UnknownIdentifierException
from syntax_tree.syntax_class.expression import SyntaxExpr, expression_factory

from syntax_tree.syntax_class.scope.data_def import SyntaxDataDefScope
from syntax_tree.syntax_class.scope.package import SyntaxPackageScope
from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
from syntax_tree.syntax_class.syntaxSymbol import SyntaxVariableSymbol, SyntaxConstSymbol
from syntax_tree.syntax_class.syntaxType import SyntaxType, SyntaxTypeSymbol
from typing import TYPE_CHECKING
from collections.abc import Iterable
from typing import TypeVar, cast
if TYPE_CHECKING:
    from syntax_tree.syntax_class.scope.clocked_block import SyntaxIfBlock

if getattr(sys, 'frozen', False):
    # 打包后的路径
    template_path = os.path.join(sys._MEIPASS, 'template')
else:
    # 开发环境下的路径
    template_path = './template'

class GenerateCode:
    def __init__(self, rootNode, mainNode, outputDir):
        self.rootNode = rootNode
        self.mainNode = mainNode
        self.outputDir = outputDir
        self.specialTypes = set()  # 保存了需要手动加入type文件的类型，比如数组,存str
        self.importedFunctions: set[SyntaxUserOp] = set()  # 保存了

        self.generated_const_symbol_names=set()# 保存了生成过的常量名字
        if not os.path.isdir(self.outputDir):
            os.makedirs(self.outputDir)

    def generate_const_file(self,userOp_order):
        # 只要写了const_block无论是否使用都会使用,从root_node开始深度遍历
        # 改了，没用到的没有生成进去
        c_content = '''#include "kcg_consts.h"\n'''
        c_content += '#ifndef _KCG_CONSTS_C_\n' \
                     '#define _KCG_CONSTS_C_\n'
        h_content = '''#ifndef _KCG_CONSTS_H_\n#define _KCG_CONSTS_H_\n#include "kcg_types.h"\n'''

        def set_base_type(param: SyntaxConstSymbol):
            if param.syntaxType.is_basic_type():
                return
            value = param.get_value()
            if value < 128:
                param.syntaxType = SyntaxType("uint8")
            elif value < 65538:
                param.syntaxType = SyntaxType("uint16")
            elif value < 4294967296:
                param.syntaxType = SyntaxType("uint32")
            else:
                param.syntaxType = SyntaxType("uint64")
            return
        for userOpScope in userOp_order:
            for size_param in userOpScope.sizeParams:
                set_base_type(size_param)
                h, c = generate_const_symbol(self,size_param)
                h_content += h
                c_content += c
        h, c = generate_const_equation(self, self.rootNode)
        h_content += h
        c_content += c

        h_content += '''#endif'''
        c_content += '''#endif'''
        with open("%s/kcg_consts.h" % (self.outputDir), 'w') as f:
            f.write(h_content)
        with open("%s/kcg_consts.c" % (self.outputDir), 'w') as f:
            f.write(c_content)

    def generate_sensor_file(self):
        pass

    def generate_types_file(self):
        src_file = os.path.join(template_path, 'kcg_types.h')
        target_file = f"{self.outputDir}/kcg_types.h"
        # write_file_from_src_to_target(src_file,target_file)

        # 中间还需要写和types相关的内容
        with open(target_file, 'w') as target:
            with open(src_file, 'r') as src:
                target.write(src.read())

    def add_code_to_types_file(self, code: str):
        target_file = f"{self.outputDir}/kcg_types.h"
        with open(target_file, "a") as target:
            target.write(code)

    # write_file(target_file,content,"a")

    def generate_assign_file(self):
        src_file =os.path.join(template_path, 'kcg_assign.h')
        target_file = f"{self.outputDir}/kcg_assign.h"
        # write_file_from_src_to_target(src_file,target_file)

    def generate_imported_types_file(self):
        pass

    @staticmethod
    def generate_imported_function_name(imported_op: SyntaxUserOp) -> str:
        package_name = imported_op.get_my_package().name
        op_name = imported_op.name
        return f"{imported_op.get_global_name()}_impl"

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
               f'#include "kcg_types.h"\n' \
               f'#include "macro_libmathext32.h"\n' \
               f'#include "macro_libmathext64.h"\n'
        for imported_op in self.importedFunctions:
            code += generate_imported_function_decl(imported_op)
        code += "#endif"

        target_file = f"{self.outputDir}/kcg_imported_functions.h"
        with open(target_file, 'w') as target:
            target.write(code)

    def generate_macro_libmathext_file(self):
        path_dict = {os.path.join(template_path, 'macro_libmathext32.h'): f"{self.outputDir}/macro_libmathext32.h",
                     os.path.join(template_path, 'macro_libmathext64.h'): f"{self.outputDir}/macro_libmathext64.h"}
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
            if not applied_expr.get_applied_op().hasInternalState: continue
            size_decl = ""
            if applied_expr.appliedOpContextList:
                size_decl = f"[{']['.join(map(str, applied_expr.appliedOpContextList))}]"
            code += f"    {applied_expr.get_applied_op().get_outC_name()} {applied_expr.appliedOpOutCName}{size_decl};\n"
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)
            if cur_node.type == "automaton":
                import syntax_tree.automaton_generate as automaton_generate
                code += automaton_generate.generate_state_nxt_for_head(cur_node)
            for para in cur_node.tmpParams:
                if para.isOutput:
                    print("para out", para.name)
                    code += f"    {para.syntaxType.change_name()} {para.name};\n"
            if isinstance(cur_node,SyntaxDataDefScope):
                for para in cur_node.localSymbolTable.values():
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
            applied_op = applied_expr.get_applied_op()
            if applied_op.isImported:
                if not had_imported_function:
                    code += '#include "macro_libmathext32.h"\n'
                    code += '#include "macro_libmathext64.h"\n'
                had_imported_function = True
                self.importedFunctions.add(applied_op)

            if applied_op.hasInternalState:
                code += f'#include "{applied_expr.get_applied_op().get_global_name()}.h"\n'
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
        target_file = f"{self.outputDir}/{global_name}.h"
        with open(target_file, "w") as target:
            target.write(head_content)

    def generate_variable_decl(self, symbol, symbol_name, depth: int = 1):
        """生成类型声明代码"""
        symbol_type = symbol.syntaxType
        c_type_name = symbol_type.change_name()
        return f"{'    ' * depth}{c_type_name} {symbol_name};\n"

    def check_and_add_special_types(self, syntaxType: SyntaxType):
        """向types文件中添加特殊类型定义"""
        real_type = syntaxType.get_real_type()
        if real_type.is_basic_type():
            return
        c_type_name = real_type.change_name()
        if c_type_name in self.specialTypes:
            return
        if real_type.type == "array":
            ele_type = real_type.get_element_type_for_array()
            self.check_and_add_special_types(ele_type)
            type_decl_code = f"typedef " \
                             f"{ele_type.change_name()} {c_type_name}[{real_type.get_size()}];\n"
            self.add_code_to_types_file(type_decl_code)
        elif real_type.type == "field_decl":
            rootPackage = real_type.scope
            global_name = rootPackage.get_global_name()
            var_name = real_type.change_name()
            precode = ""
            code = f"typedef struct {var_name} {{\n"
            for field in real_type.fields:
                k = field.name
                v: SyntaxType = field.syntaxType
                self.check_and_add_special_types(v)
                if v.type != "field_decl":
                    code += f"{v.change_name()} {k};\n"
                else:
                    tmpTypeSymbol = SyntaxTypeSymbol(f"tmp_struct_{k}", v.get_real_type(), "public")
                    precode = generate_type_symbol(self, tmpTypeSymbol, rootPackage)
                    tmpName = f"tmp_struct_{k}" if len(global_name) == 0 else f"tmp_struct_{k}_{global_name}"
                    code += f"{tmpName} {k};\n"
            code += f"\n}} {var_name};\n"
            code = precode + code
            self.add_code_to_types_file(code)
        elif real_type.type == "enum":
            name = real_type.name
            type_symbol = real_type.scope.check_and_get_type_symbol(name)
            rootPackage = real_type.scope
            global_name = rootPackage.get_global_name()
            var_name = f"{type_symbol.name}_{global_name}"
            code = f"typedef enum {var_name} {{\n"
            for idx, enum_symbol in enumerate(type_symbol.syntaxType.enumList):
                if idx != 0:
                    code += ",\n"
                code += f"{enum_symbol.name}_{global_name}"
            code += f"\n}} {var_name};\n"
            self.add_code_to_types_file(code)
        self.specialTypes.add(c_type_name)

    def generate_data_def_decl(self, data_def: SyntaxDataDefScope, depth=0) -> str:
        decl_content=""
        for name, symbol in data_def.localSymbolTable.items():
            self.check_and_add_special_types(symbol.syntaxType)
            if not symbol.isOutput:
                decl_content += self.generate_variable_decl(symbol, name, depth)
        for paraSymbol in data_def.tmpParams:
            self.check_and_add_special_types(paraSymbol.syntaxType)
            if not paraSymbol.isOutput:
                decl_content += self.generate_variable_decl(paraSymbol, paraSymbol.name, depth)
        return decl_content
    def generate_data_def_src(self, data_def: SyntaxDataDefScope, depth=0) -> str:
        # localVariable + tmpVariable
        src_content = ""
        post_content = ""
        body_content = SyntaxUserOp_generate(data_def, self, depth)
        # 加入init判断
        if data_def.initVar:
            src_content += f"{'    ' * depth}if (outC->{data_def.initVar.name}){{\n"
            for tmpSymbol in data_def.tmpParams:
                if tmpSymbol.lastExpr and tmpSymbol.isOutput:
                    src_content += f"{'    ' * (depth + 1)}outC->{tmpSymbol.name} = {tmpSymbol.lastExpr.generate_code(data_def, GenEqu())};\n"
            src_content += f"{'    ' * depth}}}\n"
        src_content += body_content
        if data_def.initVar:
            src_content += f"{'    ' * depth}outC->{data_def.initVar.name} = kcg_false;\n"


        for paraSymbol in data_def.tmpParams:
            post_code = paraSymbol.postExpr
            if post_code:
                if not isinstance(post_code, list):
                    post_content += f"{'    ' * depth}{post_code}"
                else:
                    for code in post_code:
                        post_content += f"{'    ' * depth}{code}"
        content = src_content + post_content
        return content
    def generate_data_def(self, data_def: SyntaxDataDefScope, depth=0) -> str:
        """对data_def的代码生成
        应只有最基础的功能，即data_def只作为某个代码块出现
        包括了变量声明，一般的语句生成，init过程
        有变量声明就需要有init，因为需要在
        """
        # 顺序不能变
        src=self.generate_data_def_src(data_def,depth)
        decl=self.generate_data_def_decl(data_def,depth)
        return decl+src

    def generate_src_func_file(self, node):
        global_name = node.get_global_name()
        for in_param in node.inParams:
            self.check_and_add_special_types(in_param.syntaxType)
        for out_param in node.outParams:
            self.check_and_add_special_types(out_param.syntaxType)
        src_content = f"void {global_name}(inC_{global_name} *inC,outC_{global_name} *outC){{\n"
        src_content += self.generate_data_def(node, 1)
        src_content += f"}}\n"
        print("==== src_content ====\n")
        print(src_content)
        print("======================")
        return src_content
    @staticmethod
    def call_func_recursive(depth, context_list, func_name, outc_name):
        if not context_list:
            return \
                f"{'    ' * depth}{func_name}(&({outc_name}));\n"
        _code = ""
        idx = "idx" if depth == 1 else f"idx_{str(depth)}"
        _code += f"{'    ' * (depth)}for(kcg_size {idx}=0;{idx}<{context_list[0]};{idx}++){{\n" \
                 f"{GenerateCode.call_func_recursive(depth + 1, context_list[1:], func_name, f'{outc_name}[{idx}]')}" \
                 f"{'    ' * (depth)}}}\n"
        return _code
    def generate_src_init(self, node):
        # 如果是数组情况，就需要加循环
        def generate_init_code(syntax_type: SyntaxType, param_name, depth=1) -> str:
            syntax_type = syntax_type.get_real_type()
            if syntax_type.is_basic_type():
                return f"{'    ' * depth}{param_name} = {syntax_type.generate_init_expr()};\n"
            if syntax_type.type == "array":
                _code = ""
                idx = "idx" if depth == 1 else f"idx_{str(depth)}"
                _code += f"{'    ' * (depth)}for(kcg_size {idx}=0;{idx}<{syntax_type.get_size()};{idx}++){{\n" \
                         f"{generate_init_code(syntax_type.get_element_type_for_array(), f'{param_name}[{idx}]', depth + 1)}" \
                         f"{'    ' * (depth)}}}\n"
                return _code
            if syntax_type.type == "field_decl":
                _code = ""
                for type_symbol in syntax_type.fields:
                    _code += generate_init_code(type_symbol.syntaxType, f"{param_name}.{type_symbol.name}", depth + 1)
                return _code
            if syntax_type.type == "enum":
                return f"{'    ' * depth}{param_name} = {syntax_type.generate_init_expr()};\n"
            print(syntax_type)
            raise Exception("为什么")

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
            code += generate_init_code(para.syntaxType, node.var_change_name(para.name), 1)



        for applied_expr in node.apply_exprs:
            if not applied_expr.get_applied_op().hasInternalState: continue
            code += self.call_func_recursive(1, applied_expr.appliedOpContextList,
                                     f"{applied_expr.get_applied_op().get_global_name()}_init",
                                     f"outC->{applied_expr.appliedOpOutCName}")
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)
            if cur_node.type == "automaton":
                import syntax_tree.automaton_generate as automaton_generate
                code += automaton_generate.generate_state_nxt_for_init(cur_node)

            for para in cur_node.tmpParams:
                if para.isOutput:
                    print("para init ", para.name)
                    code += generate_init_code(para.syntaxType, cur_node.var_change_name(para.name), 1)
            if issubclass(type(cur_node),SyntaxDataDefScope):
                for para in cur_node.localSymbolTable.values():
                    if para.isOutput:
                        print("para init ", para.name)
                        code += generate_init_code(para.syntaxType, cur_node.var_change_name(para.name), 1)
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
        reset_code=""
        last_gen =GenEqu()
        for applied_expr in node.apply_exprs:
            if not applied_expr.get_applied_op().hasInternalState: continue
            code += self.call_func_recursive(1, applied_expr.appliedOpContextList,
                                     f"{applied_expr.get_applied_op().get_global_name()}_reset",
                                     f"outC->{applied_expr.appliedOpOutCName}")

        def add_symbol_reset_code(param:SyntaxVariableSymbol,N:SyntaxDataDefScope)->str:
            # 很明显这就不对
            # 但是我真没招了
            if param.lastExpr is None:
                return ""
            try:
                param.lastExpr.cal_const_value(SyntaxType("any"), N)
                l_code = param.lastExpr.generate_code(N, last_gen)
                s_code = f"{assign_lhs_to_rhs_expr(N.var_change_name(param.name), l_code, [param.syntaxType], 1, N)}"
            except Exception as e:
                s_code=''
            return s_code
        for out_param in node.outParams:
            reset_code+=add_symbol_reset_code(out_param,node)
        # 最上层状态机回到初始状态
        # 重置init
        stack = deque()
        stack.append(node)
        while stack:
            cur_node = stack.pop()
            for name, child_scope in cur_node.childScopeTable.items():
                stack.append(child_scope)

            if cur_node.initVar:
                reset_code += f"    outC->{cur_node.initVar.name} = kcg_true;\n"
            for tmp_symbol in cur_node.tmpParams:
                reset_code+=add_symbol_reset_code(tmp_symbol,cur_node)
        reset_code='.'.join(last_gen.preEquations)+reset_code
        code += reset_code
        code += "}\n" \
                "#endif\n"
        return code

    def generate_src_file(self, node):
        global_name = node.get_global_name()
        src_content = f"#ifndef KCG_{node.get_global_name()}_C_\n#define KCG_{node.get_global_name()}_C_\n" \
                      f'#include "kcg_consts.h"\n#include "{global_name}.h"\n'
        # 然后include所调用的其他函数的头文件
        applied_functions = set()
        for apply_expr in node.apply_exprs:
            applied_op = apply_expr.get_applied_op()
            if applied_op is None: continue
            if applied_op in applied_functions: continue
            if applied_op.isImported: continue
            applied_functions.add(applied_op)
            src_content += f'''#include "{applied_op.get_global_name()}.h"\n'''
        src_content += self.generate_src_func_file(node)
        src_content += self.generate_src_init(node)
        src_content += self.generate_src_reset(node)
        src_content += '#endif'
        target_file = f"{self.outputDir}/{global_name}.c"
        with open(target_file, "w") as target:
            target.write(src_content)

    def generate_node_file(self, node: SyntaxUserOp):
        print(f"生成{node.name}的C代码")
        if node.isImported: return
        self.generate_src_file(node)
        self.generate_head_file(node)

    def generate_test_file(self, main_node: SyntaxUserOp):
        """一个测试类"""
        import syntax_tree.testdata.generate_test_data as generate_test_data
        length = 100

        test_code = f'#include "stdio.h"\n' \
                    f'#include "kcg_types.h"\n' \
                    f'#include "{main_node.get_global_name()}.h"\n' \
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
        generate_test_data.generate([p.syntaxType.get_real_type() for p in main_node.inParams], main_node.name,
                                    length, self.outputDir)
        with open(f"{self.outputDir}/test_data_{main_node.name}_c.txt", "r") as test_data:
            for in_param in main_node.inParams:
                data = test_data.readline().strip("\n")
                decls += f'    {in_param.syntaxType.change_name()} {in_param.name}_list[] = {{{data}}};\n'
                fills_in += assign_lhs_to_rhs_expr(f"input.{in_param.name}", f"{in_param.name}_list[i]",
                                                   [in_param.syntaxType.get_real_type()], 2, main_node)
                # fills_in += f'        input.{in_param.name}={in_param.name}_list[i];\n'
        for out_param in main_node.outParams:
            decls += f'    {out_param.syntaxType.change_name()} {out_param.name}_list[{str(length)}];\n'
            fills_out += assign_lhs_to_rhs_expr(f"{out_param.name}_list[i]", f"output.{out_param.name}",
                                                [out_param.syntaxType],
                                                2, main_node)
        test_code += decls
        test_code += "    for(int i=0;i<length;i++){\n"
        test_code += fills_in
        test_code += f'        {main_node.get_global_name()}(&input,&output);\n'
        test_code += fills_out
        test_code += '    }\n'
        test_code += f'    FILE *file = fopen("./test_data_{main_node.name}_c_out.txt","w");\n'

        def generate_param_out_code(param_type, param_name, param_list_name):
            code = ""
            param_type = param_type.get_real_type()
            if param_type.is_basic_type():
                code += f'    fprintf(file,"%s\\n","{param_name}");\n'
                code += "    for(int i=0;i<length;i++){\n"
                if param_type <= SyntaxType("float"):
                    code += f'        fprintf(file,"%f, ",{param_list_name});\n'
                else:
                    code += f'        fprintf(file,"%d, ",{param_list_name});\n'
                code += '    }\n'
                code += f'   fprintf(file,"\\n");\n'

                return code
            if param_type.type == "field_decl":
                code = ""
                for type_symbol in param_type.fields:
                    code += generate_param_out_code(type_symbol.syntaxType, f"{param_name}_{type_symbol.name}",
                                                    f"{param_list_name}.{type_symbol.name}")
                return code
            elif param_type.type == "array":
                code = ""
                sub_type = param_type.get_element_type_for_array()
                for i in range(param_type.get_size()):
                    code += generate_param_out_code(sub_type, f"{param_name}[{i}]", f"{param_list_name}[{i}]")
                return code
            elif param_type.type == "enum":
                code += f'    fprintf(file,"%s\\n","{param_name}");\n'
                code += "    for(int i=0;i<length;i++){\n"
                code += f'        fprintf(file,"%d, ",{param_list_name});\n'
                code += '    }\n'
                code += f'   fprintf(file,"\\n");\n'
                return code
            else:
                print(param_type)
                raise Exception("为什么")

        for out_param in main_node.outParams:
            test_code += generate_param_out_code(out_param.syntaxType.get_real_type(), out_param.name,
                                                 f"{out_param.name}_list[i]")
        test_code += f'    fclose(file);\n' \
                     f'}}\n'

        file_name = f"{self.outputDir}/test_{main_node.get_global_name()}.c"
        with open(file_name, "w") as file:
            file.write(test_code)

    def generate_compile_bash(self, nodes: list[SyntaxUserOp]):
        """生成一个编译bash"""
        node_names = [node.get_global_name() + '.c' for node in nodes if not node.isImported]
        content = "set - x\n" \
                  "if [ -z ${C_COMPILER} ]; then C_COMPILER=gcc; fi\n" \
                  f"$C_COMPILER -w -o {nodes[-1].name}.exec {' '.join(node_names)} kcg_consts.c" \
                  f" -lpthread test_{nodes[-1].get_global_name()}.c -lm ${{C_LIBS}}\n"
        file_name = f"{self.outputDir}/kcg_compile.sh"
        with open(file_name, "w", newline='\n') as file:
            file.write(content)


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


def generate_tmp_symbol_and_register(data_def, syntaxType: SyntaxType = None, post_fix="tmp", isOutPut=False) -> (
        SyntaxVariableSymbol, str):
    tmp_name = data_def.generate_name_for_tmp(post_fix, isOutPut)
    tmp_symbol = SyntaxVariableSymbol(tmp_name, data_def)
    tmp_symbol.syntaxType = syntaxType
    if isOutPut:
        tmp_symbol.isOutput = True
    data_def.add_tmpSymbol(tmp_symbol)
    return tmp_symbol, tmp_name


def symbol2expr(symbol, symbol_name, symbol_type, scope):
    expr = expression_factory(type="Id_expr", sub_type="Path_id", scope=scope, objects=[symbol_name])
    expr.set_symbol(symbol)
    expr.set_lhs_type([symbol_type])
    expr.set_clock_list([symbol.whenExpr])
    return expr


T = TypeVar('T')

def _ensure_list(x: T or Iterable[T]) -> list[T]:
    """单个元素→[元素]，本身已是 list 保持原样"""
    if isinstance(x, list):
        return x
    # str 是 Iterable 但这里要当成原子，单独判断
    if isinstance(x, str):
        return [x]
    # 其它可迭代对象直接展开
    if isinstance(x, Iterable):
        return list(cast(Iterable[T], x))
    return [x]

def assign_lhs_to_rhs_expr(lhs, rhs, types, depth: int, data_def,rhs_need_address_list:list[bool]=None) -> str:
    lhs_l   = _ensure_list(lhs)
    rhs_l   = _ensure_list(rhs)
    types_l = _ensure_list(types)
    if rhs_need_address_list is None:
        rhs_need_address_list=[True]*len(rhs_l)
    if not (len(lhs_l) == len(rhs_l) == len(types_l)):
        raise ValueError(f"长度不一致: {lhs_l} / {rhs_l} / {types_l}")

    indent = '    ' * depth
    lines = []
    for l, r, t,need_address in zip(lhs_l, rhs_l, types_l,rhs_need_address_list):
        if l == '_':
            continue
        if t.get_real_type().type == "array":
            lines.append(f'{indent}memcpy(&{l}, {f"&({r})" if need_address else r}, sizeof({t.change_name()}));')
        else:
            lines.append(f'{indent}{l} = {r};')
    return '\n'.join(lines) + '\n'


generate_userOp_handlers = {}


def register_userOp_handler(type_):
    def decorator(func):
        generate_userOp_handlers[type_] = func
        return func

    return decorator


@register_userOp_handler("emission")
def generate_userOp_emission(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):

    genEqu = GenEqu(depth)
    genEqu.expr = syntaxEquation.expr.generate_code(syntaxUserOp, genEqu)
    rhs_code = genEqu.expr
    if rhs_code=="kcg_true":
        emit_code = ""
        for lhs in syntaxEquation.lhs:
            emit_code += f"{'    ' * (depth)}{lhs.change_name()} = kcg_true;\n"
        code=emit_code
    else:
        emit_code = ""
        for lhs in syntaxEquation.lhs:
            emit_code += f"{'    ' * (depth + 1)}{lhs.change_name()} = kcg_true;\n"
        code = f"{'    ' * depth}if ({rhs_code}){{\n" \
               f"{emit_code}" \
               f"{'    ' * depth}}}\n"
    return code


@register_userOp_handler("simple_equation")
def generate_userOp_simple_equation(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    # out1=in1;若out1是数组或结构体，则需要使用memcpy，不能使用=。若右边是函数调用，且返回多个值，也不能直接使用=
    # if syntaxEquation.lhs[0] == "_": return ""
    # lhs_symbol = syntaxUserOp.get_localVariable_InThisAndPreEnv(syntaxEquation.lhs[0])
    # if lhs_symbol is None: lhs_symbol = syntaxUserOp.get_tmpSymbol(syntaxEquation.lhs[0])
    lhs_types = []
    lhs_clocks = []
    for lhs in syntaxEquation.lhs:
        lhs_clocks.append(lhs.get_clock())
        lhs_types.append(lhs.type_inference())
    genEqu = GenEqu(depth)
    genEqu.expr = syntaxEquation.expr.generate_code(syntaxUserOp, genEqu)
    code = ""
    code += "".join(genEqu.preEquations)
    # kcg_copy_array_int32_3(&outC->output, (array_int32_3 *) &inC->input[1]);
    lhs_codes = [lhs.change_name() for lhs in syntaxEquation.lhs]
    if len(lhs_codes) == 1:
        rhs_codes = [genEqu.expr]
    else:
        rhs_codes = genEqu.expr

    for lhs, rhs, lhs_type, clock in zip(lhs_codes, rhs_codes, lhs_types, lhs_clocks):
        assign_code = assign_lhs_to_rhs_expr(lhs, rhs, [lhs_type], depth, syntaxUserOp)
        if clock.ID == "_":
            code += assign_code
        else:
            code += f"{'    ' * depth}if ({clock.generate_code()}){{\n" \
                    f"{assign_code}" \
                    f"{'    ' * depth}}}\n"
    # code += assign_lhs_to_rhs_expr([syntaxUserOp.var_change_name(lhs) for lhs in syntaxEquation.lhs], genEqu.expr,
    #                                lhs_types, depth, syntaxUserOp)
    # code += f"{'    ' * depth}{syntaxUserOp.var_change_name(syntaxEquation.lhs[0])} = {genEqu.expr};\n"
    return code


@register_userOp_handler("assume")
def generate_userOp_assume(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    return ""


@register_userOp_handler("guarantee")
def generate_userOp_guarantee(syntaxEquation, syntaxUserOp, code_generator: GenerateCode, depth=1):
    return ""




@register_userOp_handler("control_block")
def generate_userOp_control_block(syntaxEquation, syntaxUserOp, code_generator, depth=1):
    control_block_ID = syntaxEquation.controlBlockID
    control_block = syntaxUserOp.get_childScope(control_block_ID)
    if control_block is None: raise UnknownIdentifierException(f"control_block {control_block_ID} 没有找到")
    # print("this is control_block", syntaxEquation.controlBlockID)
    if control_block.type == "automaton":
        return generate_automaton(control_block, code_generator, depth)
    elif control_block.type == "if_block":
        if_block = control_block.block
        return generate_if_block(if_block, code_generator, depth)
    elif control_block.type=="match_block":
        match_block=control_block.block
        return generate_match_block(match_block, code_generator, depth)


def generate_automaton(control_block, code_generator, depth) -> str:
    import syntax_tree.automaton_generate as automaton_generate
    code_generator.add_code_to_types_file(automaton_generate.generate_type(control_block))
    control_block.get_my_userOp().hasInternalState = True
    # print("HEAD:")
    # print(automaton_generate.generate_state_nxt_for_head(control_block))
    # print("INIT:")
    # print(automaton_generate.generate_init_symbol_for_init(control_block))
    return automaton_generate.generate_body(control_block, code_generator, depth)

def generate_match_block(match_block, code_generator, depth):
    genEqu = GenEqu(depth)

    code = f"{'    ' * (depth)}switch({match_block.switchExpr.generate_code(match_block.scope,genEqu)}){{\n"

    for case in match_block.matchList:
        syntaxPattern = case[0]
        sub_data_def:SyntaxDataDefScope = match_block.scope.get_childScope(case[1])
        pattern_code = syntaxPattern.generate_code(match_block.scope, genEqu)
        if pattern_code != '_':
            code += f"{'    ' * (depth)}case {pattern_code}:\n"
        else:
            code += f"{'    ' * (depth)}default:\n"
        code+=code_generator.generate_data_def(sub_data_def, depth + 1)
        code+= f"{'    ' * (depth)}break;\n"
    code += f"{'    ' * (depth)}}}\n"

    code=f"{''.join(genEqu.preEquations)}"+code
    return code

def generate_if_block(block: 'SyntaxIfBlock', code_generator, depth) -> str:
    scope = block.scope
    condition_genEqu = GenEqu(depth)
    condition_genEqu.expr = block.conditionExpr.generate_code(scope, GenEqu(depth))

    def generate_if_sub_block(sub_block: str or 'SyntaxIfBlock') -> str:
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
    size = typeSymbol.syntaxType.sizeExpr.generate_code(rootPackage, genEqu)
    global_name = rootPackage.get_global_name()
    var_name = typeSymbol.name if len(global_name) == 0 else f"{typeSymbol.name}_{global_name}"
    code = f"typedef kcg_int{size} {var_name};\n"
    print("=== signed ===\n")
    print(code)
    return code


@register_syntax_type_handler(r"^unsigned")
def generate_syntax_type_unsigned(typeSymbol, rootPackage):
    genEqu = GenEqu()
    size = typeSymbol.syntaxType.sizeExpr.generate_code(rootPackage, genEqu)
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
def generate_syntax_type_enum(code_generator, typeSymbol, rootPackage):
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
def generate_syntax_type_field_decl(code_generator, typeSymbol, rootPackage):
    global_name = rootPackage.get_global_name()
    symbol_type = typeSymbol.syntaxType.get_real_type()
    var_name = symbol_type.change_name()
    precode = ""
    code = f"typedef struct {var_name} {{\n"
    for field in symbol_type.fields:
        k = field.name
        v: SyntaxType = field.syntaxType
        code_generator.check_and_add_special_types(v)
        if v.type != "field_decl":
            code += f"{v.change_name()} {k};\n"
        else:
            tmpTypeSymbol = SyntaxTypeSymbol(f"tmp_struct_{k}", v.get_real_type(), "public")
            precode = generate_type_symbol(code_generator, tmpTypeSymbol, rootPackage)
            tmpName = f"tmp_struct_{k}" if len(global_name) == 0 else f"tmp_struct_{k}_{global_name}"
            code += f"{tmpName} {k};\n"
    code += f"\n}} {var_name};\n"
    code = precode + code
    return code


@register_syntax_type_handler(r"^array")
def generate_syntax_type_list(code_generator, typeSymbol, rootPackage):
    code_generator.check_and_add_special_types(typeSymbol.syntaxType)
    # print("this is array ", typeSymbol.name, typeSymbol.syntaxType.get_size(),
    #       typeSymbol.syntaxType.get_element_type_for_array())
    # type_, code_ = generate_syntax_type_list_recursive(typeSymbol.syntaxType, rootPackage, typeSymbol.name)
    # code_ += f"typedef {type_} {typeSymbol.name};\n"
    # print("==== code_\n")
    # print(code_)
    return ''


@register_syntax_type_handler(r"(bool|char|int\d+|uint\d+|float\d+)")
def generate_syntax_type_other(code_generator, typeSymbol, rootPackage):
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

def generate_const_symbol(code_generator,const_symbol):
    global_name = const_symbol.scope.get_global_name()
    symbol_type = const_symbol.syntaxType.change_name()
    symbol_name = const_symbol.name if len(global_name) == 0 else f"{const_symbol.name}_{global_name}"
    if symbol_name in code_generator.generated_const_symbol_names:
        return "",""
    code_generator.generated_const_symbol_names.add(symbol_name)
    symbol_h = ""
    symbol_c = ""
    if const_symbol.isImported:
        symbol_h += f'''
        #ifndef {symbol_name}\n
        #define {symbol_name} {symbol_name}\n
        extern const {symbol_type} {symbol_name};\n
        #endif\n
       '''
    else:

        symbol_h += f"extern const {symbol_type} {symbol_name};\n"
        symbol_c += f"const {symbol_type} {symbol_name}={const_symbol.generate_code_const()};\n"
    return symbol_h, symbol_c
def generate_const_equation(code_generator, rootPackage):
    h_content = ""
    c_content = ""


    for name, constSymbol in rootPackage.constSymbolTable.items():
        if not constSymbol.used: continue
        if constSymbol.syntaxType.get_real_type().type == "enum": continue
        code_generator.check_and_add_special_types(constSymbol.syntaxType)
        h, c = generate_const_symbol(code_generator,constSymbol)
        h_content += h
        c_content += c

    for _, packageScope in rootPackage.childScopeTable.items():
        h, c = generate_const_equation(code_generator, packageScope)
        h_content += h
        c_content += c

    return h_content, c_content


def generate_type_symbol(code_generator, typeSymbol, rootPackage):
    real_type = typeSymbol.syntaxType.get_real_type()
    if real_type.change_name() in code_generator.specialTypes:
        return ""

    type_ = real_type.type
    for regex, func in generate_syntax_type_handlers.items():
        if regex.match(type_):
            code = func(code_generator, typeSymbol, rootPackage)
            code_generator.specialTypes.add(real_type.change_name())
            return code

    else:
        raise Exception(f"{type_}怎么没有啊")


def generate_type_block(code_generator, rootPackage):
    h_content = ""
    for _, packageScope in rootPackage.childScopeTable.items():
        h_content += generate_type_block(code_generator, packageScope)
    for _, typeSymbol in rootPackage.typeSymbolTable.items():
        h_content += generate_type_symbol(code_generator, typeSymbol, rootPackage)
    return h_content


def generate(main_operator, root_scope, userOp_order, output_path, need_test_file):
    gen = GenerateCode(root_scope, main_operator, output_path)

    # gen.generate_main_file()
    gen.generate_types_file()

    for op in userOp_order:
        gen.generate_node_file(op)
    gen.generate_imported_functions_file()
    gen.generate_const_file(userOp_order)
    gen.add_code_to_types_file("#endif\n")  # 结束
    gen.generate_macro_libmathext_file()
    if need_test_file:
        print(f"生成测试类:{userOp_order[-1].name}")
        gen.generate_test_file(userOp_order[-1])
        gen.generate_compile_bash(userOp_order)
