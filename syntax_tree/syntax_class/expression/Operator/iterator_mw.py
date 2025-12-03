from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr, \
    symbol2expr, GenEqu
from syntax_tree.scade_type_inference import type_inference_on_groups
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr, expression_factory
from syntax_tree.syntax_class.expression.expr_common import int_to_expression
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each, union_rhsLists
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_iterator_mw(SyntaxExpr):
    iterator_op:str
    '''map fold mapfold以及带i的形式'''
    sub_operator:SyntaxExpr
    '''子表达式'''
    array_length_expr:SyntaxExpr
    '''迭代的数组长度'''
    map_index:int
    '''前n个参数视为fold，后面视为map'''
    init_cond_expr:SyntaxExpr
    '''开始循环的条件表达式'''
    default_expr:SyntaxExpr
    '''当cond_expr为false时，填充的默认表达式（fold没有这个表达式）'''
    @property
    def is_fold(self):
        return self.iterator_op.startswith("foldw")
    @property
    def is_map(self):
        return self.iterator_op.startswith("mapw")
    @property
    def is_mapfold(self):
        return self.iterator_op.startswith("mapfoldw")
    @property
    def need_output_cond(self):
        return self.is_fold or self.is_map
    @property
    def has_i(self):
        return self.iterator_op.endswith("i")
    def post_process(self, data_def):
        # 他们会对调用的op有要求
        # 在类型推导里做具体的校验
        # 但是需要改变一下给subOp的参数
        def merge_rhs(rhs_list_list)-> set[str]:
            # 全部融合
            out_set=set()
            for rhs_list in rhs_list_list:
                for rhs in rhs_list:
                    out_set|=rhs
            return out_set
        result =self.sub_operator.post_process(data_def)
        self.rhsList = add_rhs_to_each(self.array_length_expr.rhsList, self.sub_operator.rhsList)
        self.rhsList = add_rhs_to_each(self.init_cond_expr.rhsList, self.rhsList)
        # 所有输入依赖所有输出
        if self.is_fold:
            expr_list=(self.array_length_expr,self.sub_operator,self.init_cond_expr)
        else:
            expr_list=(self.array_length_expr,self.sub_operator,self.init_cond_expr,self.default_expr)
        rhs=merge_rhs([expr.rhsList for expr in expr_list])
        self.returnNum = self.sub_operator.returnNum
        # mapfold会输出最终的cond,其他情况就不会
        # map和fold中，子op多输出一个cond，然后少输出一个idx，所以不变
        if self.is_mapfold:
            self.returnNum+=1
        self.rhsList=[rhs]*self.returnNum
    def type_inference(self, lhs_type_list, userOp):
        self.array_length_expr.type_inference([SyntaxType("int32")], userOp)
        self.init_cond_expr.type_inference([SyntaxType("bool")], userOp)
        required_length = self.array_length_expr.cal_const_value(SyntaxType("int32"), self.scope).value

        # 这里多了一个idx，一个cond
        if self.is_mapfold:
            idx_lhs=lhs_type_list[0]
            cond_lhs=lhs_type_list[1]
            non_map_lhs_list = lhs_type_list[2:self.map_index+2]
            map_lhs_list = lhs_type_list[self.map_index+2:]
        else:
            idx_lhs=lhs_type_list[0]
            cond_lhs=SyntaxType("bool")
            non_map_lhs_list = lhs_type_list[1:self.map_index+1]
            map_lhs_list = lhs_type_list[self.map_index+1:]
        for lhs_type in map_lhs_list:
            if lhs_type.get_size() != required_length:
                raise TypeMismatchException(lhs_type, f"尺寸为{required_length}的数组", userOp)
        # 有i的情况就是给子operator传递一个idx参数
        # 没有i就不传递这个idx
        # 不影响输出的参数
        sub_map_list = [lhs_type.get_element_type_for_array() for lhs_type in map_lhs_list]
        sub_lhs_list = [cond_lhs] + non_map_lhs_list + sub_map_list

        if not self.is_fold:
            self.default_expr.type_inference(sub_map_list,userOp)
        given_lhs_list = self.sub_operator.type_inference(sub_lhs_list, userOp)
        # todo sub_op与默认表达式在map领域进行推导

        given_cond_lhs=given_lhs_list[0]
        given_non_map_lhs_list=given_lhs_list[1:self.map_index+1]
        # 拿到下层推理后的真实类型，再包装后返还
        if self.is_fold:
            actual_lhs_list = [idx_lhs, given_cond_lhs] + given_non_map_lhs_list
        else:
            given_map_lhs_list=given_lhs_list[self.map_index+1:]
            actual_lhs_list = [idx_lhs,given_cond_lhs]+given_non_map_lhs_list+[
                SyntaxType(tar_type="array", scope=userOp).set_element_and_size(t, required_length)
                for t in given_map_lhs_list]
        self.set_lhs_type(actual_lhs_list)
        context_list = self.sub_operator.appliedOpContextList.copy()
        context_list.insert(0, required_length)
        apply_userOp = self.get_applied_op()
        if apply_userOp is not None:
            self.add_applied_Op(apply_userOp, context_list)
        # todo 考虑到default表达式，可能返回值有不同的时钟？
        self.set_clock_list(self.sub_operator.lhsClockList)
        return self.lhsTypeList
    def generate_code(self, data_def, genEqu):

        depth = genEqu.depth
        map_idx = self.map_index
        # 先对初始条件进行判断
        init_cond_code=self.init_cond_expr.generate_code(data_def,genEqu)
        cond_symbol,cond_name=generate_tmp_symbol_and_register(data_def,SyntaxType("bool"),"cond")
        # 用来输出
        idx_out_symbol,idx_out=generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx_out")
        # 遍历数组
        tmp_idx_symbol, tmp_idx = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")



        core_code = ""
        fold_symbols = list()
        # 给属于fold的变量赋初始值
        pre_code=""
        for i in range(map_idx):
            # 这边都是fold
            fold_symbol, fold_name = generate_tmp_symbol_and_register(data_def, self.lhsTypeList[i], "fold")
            fold_symbols.append(fold_symbol)
            pre_code += assign_lhs_to_rhs_expr(fold_name, self.paramExprs[i].generate_code(data_def, genEqu),
                                               [self.lhsTypeList[i]], depth, data_def)
        # map变量的声明和赋值操作
        # 这些都是输入变量
        def get_element_for_parameters(parameters: list[SyntaxExpr], data_def, depth, idx_name, tmp_post_fix="tmp") -> (
                str, list[SyntaxExpr]):
            """返回一个precode和新参数表达式列表"""
            sub_parameters = list()
            genEqu = GenEqu(depth)
            for parameter in parameters:
                para_type = parameter.lhsTypeList[0]
                tmp_symbol, tmp_name = generate_tmp_symbol_and_register(data_def,
                                                                        para_type.get_element_type_for_array(),
                                                                        tmp_post_fix)
                para_code = parameter.generate_code(data_def, genEqu)
                pre_code = assign_lhs_to_rhs_expr(tmp_name, para_code + f"[{idx_name}]", [tmp_symbol.syntaxType],
                                                  genEqu.depth, data_def)
                genEqu.add_preEquations(pre_code)
                sub_parameters.append(symbol2expr(tmp_symbol, tmp_name, para_type, data_def))
            return "".join(genEqu.preEquations), sub_parameters
        map_pre_codes, sub_params_map = get_element_for_parameters(self.paramExprs[map_idx:], data_def, depth + 2, tmp_idx,
                                                                   "map")
        if self.has_i:
            sub_symbols=[tmp_idx_symbol]+fold_symbols
        else:
            sub_symbols =fold_symbols
        sub_params = [symbol2expr(symbol, symbol.name, symbol.syntaxType, data_def) for symbol in
                      sub_symbols] + sub_params_map
        sub_genEqu = GenEqu(depth + 2)
        self.sub_operator.set_applied_outC_name(f"{self.appliedOpOutCName}[{tmp_idx}]")
        self.sub_operator.set_params(sub_params)
        sub_operator_code = self.sub_operator.generate_code(data_def,sub_genEqu)
        # sub_params, data_def, sub_genEqu, applied_outc_name)
        # 上面就完成了所有子operator的构造过程
        # 下面要把子operator的输出和对应的输入匹配起来
        map_out_symbols = list()
        for i in range(map_idx+2, len(self.lhsTypeList)):
            map_out_symbol, map_out_name = generate_tmp_symbol_and_register(data_def, self.lhsTypeList[i],
                                                                            "map_out")
            map_out_symbols.append(map_out_symbol)
        # 构建赋值的左值名字列表
        # 和子operator的返回值一一对应
        lhs_types = self.lhsTypeList
        lhs_types = [lhs_types[i] if i < map_idx+2 else lhs_types[i].get_element_type_for_array() for i in
                     range(len(lhs_types))]

        if self.is_fold:
            lhs_codes = [idx_out_symbol.name,cond_symbol.name]+[symbol.name for symbol in fold_symbols]
        else:
            lhs_codes = [idx_out_symbol.name,cond_symbol.name]+[symbol.name for symbol in fold_symbols] + [symbol.name + f"[{tmp_idx}]" for symbol in
                                                                map_out_symbols]
        post_assign_code = assign_lhs_to_rhs_expr(lhs_codes, [f"(kcg_int32) ({tmp_idx_symbol.name} + 1)"]+sub_operator_code, lhs_types, depth + 2, data_def)

        array_length=self.array_length_expr.cal_const_value(SyntaxType('integer'),data_def).value
        # 进行for循环
        core_code += f"{'    ' * (depth+1)}for ({tmp_idx} = 0; {tmp_idx} < {array_length}; {tmp_idx}++) {{\n" \
                    f"{map_pre_codes}" \
                    f"{''.join(sub_genEqu.preEquations)}" \
                    f"{post_assign_code}" \
                     f"{'    ' * (depth+2)}if (!{cond_symbol.name}){{break;}}\n"
        core_code += f"{'    ' * (depth+1)}}}\n"


        cond_assign_true=f"{'    '*(depth+1)}{cond_name} = kcg_true;\n" if self.is_mapfold else ""
        cond_assign_false=f"{'    '*(depth+1)}{cond_name} = kcg_false;\n" if self.is_mapfold else ""
        pre_code+=f"{'    ' * (depth)}if ({init_cond_code}){{\n" \
                  f"{cond_assign_true}" \
                  f"{core_code}" \
                  f"{'    '*depth}}}else {{\n" \
                  f"{cond_assign_false}" \
                  f"{'    '*(depth+1)}{idx_out} = kcg_lit_int32(0);\n" \
                  f"{'    '*depth}}}\n"
        if not self.is_fold:
            default_idx_symbol, default_idx_name = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"),
                                                                                    "idx")
            default_rhs_code = self.default_expr.generate_code(data_def, genEqu)
            default_assign_code = assign_lhs_to_rhs_expr(
                [symbol.name + f"[{default_idx_name}]" for symbol in map_out_symbols], default_rhs_code,
                lhs_types[map_idx + 2:], depth + 1, data_def)
            pre_code +=\
                  f"{'    ' * (depth)}for ({default_idx_name} = {idx_out}; {default_idx_name} < {array_length}; {default_idx_name}++){{\n" \
                  f"{default_assign_code}" \
                  f"{'    '*depth}}}\n"
        # for (idx = / * idx= * / (kcg_size) outC->idx; idx < 3; idx++) {
        # outC->v[idx] = kcg_lit_int32(5);
        # }
        genEqu.add_preEquations(pre_code)
        if self.is_mapfold:
            out_symbols = [idx_out_symbol,cond_symbol]+fold_symbols + map_out_symbols
        else:
            out_symbols = [idx_out_symbol] + fold_symbols + map_out_symbols
        return [symbol.name for symbol in out_symbols]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.iterator_op=objects[0]
        self.sub_operator=objects[2]
        self.array_length_expr=objects[3]
        if self.iterator_op.startswith("mapfoldw"):
            self.map_index = self.objects[1]# 参数中指定
            self.default_expr=objects[5]
        elif self.iterator_op.startswith("mapw"):
            self.map_index = 0
            self.default_expr=objects[5]
        else:
            # iterator_op.startswith("foldw")
            self.map_index = 1
            # yes，一个累加参数后面接很多map参数
            # 如果有很多累加参数就会变成mapfold
            # foldw没有默认表达式
            self.default_expr=None
        self.init_cond_expr=objects[4]

    def set_param_expr(self,param_expr):
        sub_param_expr=expression_factory("generalized","get",self.scope,
                                          [param_expr,self.array_length_expr,self.map_index])
        if self.has_i:
            sub_param_expr=expression_factory("List_expr","List_expr",self.scope,
                                          [[int_to_expression(0,self.scope),sub_param_expr]])
        else:
            sub_param_expr=expression_factory("List_expr","List_expr",self.scope,
                                              [[sub_param_expr]])
        self.sub_operator.set_param_expr(sub_param_expr)
    def set_params(self,params:list['SyntaxExpr']):
        self.paramExprs=params
    def get_applied_op(self):
        return self.sub_operator.get_applied_op()
