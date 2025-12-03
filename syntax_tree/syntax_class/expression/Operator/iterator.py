from syntax_tree.scade_generate import generate_tmp_symbol_and_register, assign_lhs_to_rhs_expr, \
    symbol2expr, GenEqu
from syntax_tree.syntax_class.Exceptions import TypeMismatchException
from syntax_tree.syntax_class.expression import SyntaxExpr, expression_factory
from syntax_tree.syntax_class.expression.expr_common import int_to_expression
from syntax_tree.syntax_class.hasRhs import add_rhs_to_each
from syntax_tree.syntax_class.syntaxType import SyntaxType


class Operator_iterator(SyntaxExpr):
    iterator_op:str
    '''map fold mapfold以及带i的形式'''
    sub_operator:SyntaxExpr
    '''子表达式'''
    array_length_expr:SyntaxExpr
    '''迭代的数组长度'''
    map_index:int
    '''前n个参数视为fold，后面视为map'''
    @property
    def has_i(self):
        return self.iterator_op.endswith("i")
    @property
    def is_fold(self):
        return self.iterator_op.startswith("foldw")
    @property
    def is_map(self):
        return self.iterator_op.startswith("mapw")
    @property
    def is_mapfold(self):
        return self.iterator_op.startswith("mapfoldw")
    def post_process(self, data_def):
        # 很神奇吧，iterator不修改返回的参数数量
        # 他们会对调用的op有要求
        # 在类型推导里做具体的校验
        # 但是需要改变一下给subOp的参数
        result =self.sub_operator.post_process(data_def)
        self.rhsList=add_rhs_to_each(self.array_length_expr.rhsList,self.sub_operator.rhsList)
        self.returnNum=self.sub_operator.returnNum
        return result
    def type_inference(self, lhs_type_list, userOp):
        self.array_length_expr.type_inference([SyntaxType("integer")], userOp)
        required_length = self.array_length_expr.cal_const_value(SyntaxType("int32"), self.scope).value

        non_map_lhs_list = lhs_type_list[:self.map_index]
        map_lhs_list = lhs_type_list[self.map_index:]
        for lhs_type in map_lhs_list:
            if lhs_type.get_size() != required_length:
                raise TypeMismatchException(lhs_type, f"尺寸为{required_length}的数组", userOp)

        sub_lhs_list = non_map_lhs_list+[lhs_type.get_element_type_for_array() for lhs_type in map_lhs_list]
        given_lhs_list = self.sub_operator.type_inference(sub_lhs_list, userOp)
        given_non_map_lhs_list=given_lhs_list[:self.map_index]
        given_map_lhs_list=given_lhs_list[self.map_index:]
        # 拿到下层推理后的真实类型，再包装后返还
        actual_lhs_list = given_non_map_lhs_list+[
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
        # 先生成一个临时变量遍历数组
        tmp_idx_symbol, tmp_idx = generate_tmp_symbol_and_register(data_def, SyntaxType("int32"), "idx")
        pre_code = ""
        fold_symbols = list()
        # 给属于fold的变量赋初始值
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
        map_pre_codes, sub_params_map = get_element_for_parameters(self.paramExprs[map_idx:], data_def, depth + 1, tmp_idx,
                                                                   "map")
        sub_params = [symbol2expr(symbol, symbol.name, symbol.syntaxType, data_def) for symbol in
                      fold_symbols] + sub_params_map
        if self.has_i:
            sub_params.insert(0,symbol2expr(tmp_idx_symbol,tmp_idx,tmp_idx_symbol.syntaxType,data_def))
        sub_genEqu = GenEqu(depth + 1)
        self.sub_operator.set_applied_outC_name(f"{self.appliedOpOutCName}[{tmp_idx}]")
        self.sub_operator.set_params(sub_params)
        sub_operator_code = self.sub_operator.generate_code(data_def,sub_genEqu)
        # sub_params, data_def, sub_genEqu, applied_outc_name)
        # 上面就完成了所有子operator的构造过程
        # 下面要把子operator的输出和对应的输入匹配起来
        map_out_symbols = list()
        for i in range(map_idx, len(self.lhsTypeList)):
            map_out_symbol, map_out_name = generate_tmp_symbol_and_register(data_def, self.lhsTypeList[i],
                                                                            "map_out")
            map_out_symbols.append(map_out_symbol)
        # 构建赋值的左值名字列表
        # 和子operator的返回值一一对应
        lhs_types = self.lhsTypeList
        lhs_types = [lhs_types[i] if i < map_idx else lhs_types[i].get_element_type_for_array() for i in
                     range(len(lhs_types))]
        lhs_codes = [symbol.name for symbol in fold_symbols] + [symbol.name + f"[{tmp_idx}]" for symbol in
                                                                map_out_symbols]
        post_assign_code = assign_lhs_to_rhs_expr(lhs_codes, sub_operator_code, lhs_types, depth + 1, data_def)

        # 进行for循环
        pre_code += f"{'    ' * depth}for ({tmp_idx} = 0; {tmp_idx} < {self.array_length_expr.cal_const_value(SyntaxType('integer'),data_def).value}; {tmp_idx}++) {{\n" \
                    f"{map_pre_codes}" \
                    f"{''.join(sub_genEqu.preEquations)}" \
                    f"{post_assign_code}"
        pre_code += f"{'    ' * depth}}}\n"
        genEqu.add_preEquations(pre_code)
        out_symbols = fold_symbols + map_out_symbols
        return [symbol.name for symbol in out_symbols]
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type, subtype, scope, objects, returnNum)
        self.iterator_op=objects[0]
        self.sub_operator=objects[2]
        self.array_length_expr=objects[3]
        if self.iterator_op.startswith("mapfold"):
            self.map_index = self.objects[1]# 参数中指定
        elif self.iterator_op.startswith("map"):
            self.map_index = 0
        else:
            # iterator_op.startswith("fold")
            self.map_index = 1
    def set_param_expr(self,param_expr):
        iterator_op=self.iterator_op
        sub_param_expr=expression_factory("generalized","get",self.scope,
                                          [param_expr,self.array_length_expr,self.map_index])
        if iterator_op.endswith("i"):
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
