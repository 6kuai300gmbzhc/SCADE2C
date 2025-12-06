import copy

from syntax_tree.exclude_from_deepcopy import exclude_from_deepcopy
from syntax_tree.scade_generate import GenerateCode, assign_lhs_to_rhs_expr, generate_tmp_symbol_and_register
from syntax_tree.scade_type_inference import type_inference_userOp
from syntax_tree.syntax_class.Exceptions import ParamMismatcheException, UnknownIdentifierException, \
    TypeMismatchException, CanNotInstantiateException
from syntax_tree.syntax_class.expression import SyntaxExpr

from syntax_tree.syntax_class.expression.clock_expr import SyntaxClockExpr
from syntax_tree.syntax_class.expression.const_value import ConstValue
from syntax_tree.syntax_class.scope.userOp import SyntaxUserOp
from syntax_tree.syntax_class.syntaxType import SyntaxType
def generate_and_register_inC(data_def, applied_userOp):
    """生成一个inc对象并注册,inc肯定是一个临时变量"""
    inc_type = SyntaxType("other")
    inc_type.value = applied_userOp.get_inC_name()
    inc_symbol, inc_name = generate_tmp_symbol_and_register(data_def, inc_type,
                                                            applied_userOp.get_global_name() + "_inC")
    return inc_name
def generate_and_register_outC(data_def, applied_userOp):
    # 没内存，就要自己生成一个临时变量outC
    outc_type = SyntaxType("other")
    outc_type.value = applied_userOp.get_outC_name()
    outc_symbol, outC_name = generate_tmp_symbol_and_register(data_def, outc_type,
                                                              applied_userOp.get_global_name() + "_outC")
    return outC_name

def extend_rhs_list(rhs_list_list: list[list[set[str]]]) -> list[set[str]]:
    """把右值列表连接起来"""
    output = list()
    for rhs_list in rhs_list_list:
        output.extend(rhs_list)
    return output
# 类型有点太长了
instantiated_op_dict: dict[SyntaxUserOp, list[list[dict[str, SyntaxType], list[ConstValue], SyntaxUserOp]]] = dict()
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
def deepcopy_userOp(userOp):
    """天才"""
    tmp_prev_scope = userOp.prevScope
    userOp.prevScope = None
    copied_userOp = copy.deepcopy(userOp)
    userOp.prevScope = tmp_prev_scope
    copied_userOp.prevScope = tmp_prev_scope
    return copied_userOp
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
    if not all(t.is_type_determined() for t in instantiate_dict.values()):
        raise CanNotInstantiateException(userOp, param_expr, "有模板参数无法推导为基本类型")
    print(f"获取的实例化字典为:{instantiate_dict}")

    instantiate_sizes = list()
    for size_expr, size_param in zip(size_exprs, userOp.sizeParams):
        const_value = size_expr.cal_const_value(SyntaxType('integer'), userOp)
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

    for size_expr,size_symbol, size_param in zip(size_exprs,instantiate_sizes, instantiate_userOp.sizeParams):
        size_param.set_value(size_symbol.value)
        size_param.syntaxType = size_symbol.type
        size_param.valueExpr=size_expr
        size_expr.type_inference([size_param.syntaxType],userOp)

    if len(size_exprs) != len(instantiate_userOp.sizeParams):
        raise CanNotInstantiateException(instantiate_userOp, size_exprs, "输入的sizedecl长度与函数声明的不一样")

    instantiate_userOp.name = generate_instantiate_name(userOp, instantiate_dict, instantiate_sizes)
    instantiate_userOp.get_my_package().add_userOp(instantiate_userOp)
    print(f"生成实例化函数{instantiate_userOp.get_global_name()}")
    add_instantiated_op(userOp, instantiate_dict, instantiate_sizes, instantiate_userOp)
    userOp.add_instantiatedOp(instantiate_userOp)
    return instantiate_userOp
def add_instantiated_op(userOp, instantiate_dict, instantiate_sizes, instantiated_op) -> None:
    instantiated_op_dict.get(userOp).append([instantiate_dict, instantiate_sizes, instantiated_op])
@exclude_from_deepcopy('appliedOp')
class Operator_Path_id(SyntaxExpr):
    appliedOp:SyntaxUserOp
    '''要调用的op'''
    paramExpr:SyntaxExpr
    '''参数表达式，应该是一个list表达式'''
    call_clock:SyntaxClockExpr
    '''调用此op的时钟表达式'''
    def post_process(self, data_def: 'SyntaxUserOp'):
        self.paramExpr.post_process(data_def)
        self.appliedOp=data_def.check_and_get_userOp(self.objects[0])
        if not self.appliedOp:
            raise UnknownIdentifierException(f"{data_def.get_global_name()}找不到{self.objects[0]}")
        params: list[set[str]] = extend_rhs_list([expr.rhsList for expr in self.paramExpr.objects[0]])
        # 找到了之后，根据这个函数的依赖关系确定这个表达式的依赖关系
        # 如果这个函数没有返回值，就直接返回输入的参数
        # 如果有返回值，就看一眼对应的参数，根据依赖表确定情况
        if len(self.appliedOp.inParams) != len(params):
            raise ParamMismatcheException(f"{self}在函数调用时参数数量不匹配,在{data_def.get_global_name()}内")
        for size_expr in self.objects[1]:
            size_expr.post_process(data_def)
        rhs_list:list[set[str]] = list()
        if not self.appliedOp.outParams:
            rhs_set:set[str] = set()
            for i in self.appliedOp.output2inputDependents[0]:
                rhs_set.update(params[i])
            rhs_list.append(rhs_set)
        else:
            for i in range(len(self.appliedOp.output2inputDependents)):
                rhs_set:set[str] = set()
                out_dependent_list = self.appliedOp.output2inputDependents[i]
                for j in out_dependent_list:
                    rhs_set.update(params[j])
                rhs_list.append(rhs_set)
        self.returnNum, self.rhsList = len(self.appliedOp.outParams), rhs_list
    def type_inference(self, lhs_type_list: list['SyntaxType'], data_def:'SyntaxUserOp'):
        # 进行实例化
        # 校验一下，要求的类型是不是和目标op返回的类型一样
        # 这里有可能左值类型并非基本类型，所以仅当可以推断出来一个基本类型时才去进行实例化操作
        input_types = [param.syntaxType for param in self.appliedOp.inParams]
        self.paramExpr.type_inference(input_types, data_def)
        # 检查并进行模板实例化
        if self.appliedOp.isTemplate():
            self.appliedOp = instantiate_template_function(self.appliedOp, self.paramExpr.lhsTypeList, input_types, self.paramExpr,
                                                           self.objects[1])
            # 实例化后再推理一边，因为实例化后函数的输入参数类型变了
            input_types = [param.syntaxType for param in self.appliedOp.inParams]
            self.paramExpr.type_inference(input_types, data_def)

        returned_types = [param.syntaxType for param in self.appliedOp.outParams]
        if not all(g <= r for g, r in zip(returned_types, lhs_type_list)):
            raise TypeMismatchException(f"{self.appliedOp.get_global_name()}有type{returned_types}", lhs_type_list, data_def)

        type_inference_userOp(self.appliedOp)

        self.set_lhs_type(returned_types)
        self.add_applied_Op(self.appliedOp, [])
        self.set_lhs_type(returned_types)


        param_clock_list=self.paramExpr.lhsClockList
        if not param_clock_list:
            self.set_clock_list([out_param.whenExpr for out_param in self.appliedOp.outParams])
            self.call_clock=SyntaxClockExpr.init_clock_base(data_def.get_my_userOp())
            return self.lhsTypeList

        param_clock_dict:dict[str,SyntaxClockExpr]=dict()
        # 把函数内部参数时钟和输入的参数时钟对应起来
        for param_clock,in_param in zip(param_clock_list, self.appliedOp.inParams):
            in_param_clock_str=str(in_param.whenExpr)
            if (existed_clock:=param_clock_dict.get(in_param_clock_str)) is None:
                param_clock_dict[in_param_clock_str]=param_clock
            else:
                if not existed_clock.fit(param_clock):
                    raise Exception(f"在调用函数{self.appliedOp.name}时，{in_param.name}的输入时钟存在冲突")

        def get_fast_clock(clock_list):
            if len(clock_list)==0:
                return SyntaxClockExpr.init_clock_base(data_def.get_my_userOp())
            fast_clock=clock_list[0]
            for cur_clock in clock_list[1:]:
                if cur_clock.ID=="_":
                    fast_clock=cur_clock
            print(self)
            print(param_clock_list)
            print("看一下clock对不对")
            return fast_clock

        self.call_clock=get_fast_clock(param_clock_list)
        # 最快时钟就是调用此函数的时钟，也是其输出参数的基准时钟

        out_clock_list=list()
        for out_param in self.appliedOp.outParams:
            if out_param.whenExpr.ID=="_":
                curres_clock=param_clock_dict.get(str(out_param.whenExpr))
                if curres_clock is None:
                    raise Exception("不对！！！")
                out_clock_list.append(curres_clock)
            else:
                raise Exception(f"{self.appliedOp.get_global_name()}不是内联函数，输出参数不可为有时钟的对象")
                # # todo 这里需要参考scade的clock类型变量进行校验
                # # todo 时钟为输入参数的情况
                # out_clock_list.append(out_param.whenExpr)
        self.set_clock_list(out_clock_list)


        return self.lhsTypeList
    def generate_code(self, syntaxUserOp:'SyntaxUserOp', genEqu:'GenEqu'):
        # 先看一眼cache再说
        my_op=syntaxUserOp.get_my_userOp()
        if (cache:=my_op.opReturnSymbolCache.get(self.appliedOp.get_outC_name())) is not None:
            if cached_symbol_codes:=cache[1]:
                return cached_symbol_codes

        # 这里是函数调用语句
        # 生成一个inC结构体，将输入参数填入
        # 生成一个空outC结构体
        # 如果是node，则这个outC去当前函数的outC里面取
        # 如果是function，就直接初始化一个，说实话有点恶心
        # 结束调用后，把outC里面的结果拿出来进行进一步赋值操作
        parameters=self.paramExprs
        global_name = self.appliedOp.get_global_name()
        if self.appliedOp.isImported:
            # 拿一下输入参数对应代码
            param_code = ", ".join(param.generate_code(syntaxUserOp, genEqu) for param in parameters)
            applied_code = GenerateCode.generate_imported_function_name(self.appliedOp)
            applied_code += f"({param_code})"

            # 把参数赋值
            # 这里把是否需要&给处理了，要不然后面会很麻烦
            out_type=self.appliedOp.outParams[0].syntaxType
            out_param,out_name=generate_tmp_symbol_and_register(syntaxUserOp,out_type)
            genEqu.add_preEquations(assign_lhs_to_rhs_expr(out_name,applied_code,out_type,genEqu.depth,syntaxUserOp,rhs_need_address_list=[False]))
            return out_name

        code = ""
        # inC需要自己进行构造，outC可能出现在此函数的outC中
        tmp_inC_name = generate_and_register_inC(syntaxUserOp, self.appliedOp)
        if self.appliedOp.hasInternalState:
            tmp_outC_name = f"outC->{self.appliedOpOutCName}"
        else:
            tmp_outC_name = generate_and_register_outC(syntaxUserOp, self.appliedOp)
        depth=genEqu.depth
        need_clock=self.call_clock.ID!="_"
        if need_clock:
            depth+=1
            code+=f"{'    '*(depth-1)}if ({self.call_clock.generate_code()}){{\n"


        # 填充inc结构体
        for idx, param in enumerate(parameters):
            param_code = param.generate_code(syntaxUserOp, genEqu)
            in_param = self.appliedOp.inParams[idx]
            code += assign_lhs_to_rhs_expr(f"{tmp_inC_name}.{in_param.name}", param_code, [in_param.syntaxType],
                                           depth, syntaxUserOp)

        # 进行函数调用
        code += f"{'    ' * depth}{global_name}(&{tmp_inC_name}, &{tmp_outC_name});\n"
        if need_clock:
            code+=f"{'    '*(depth-1)}}}\n"
        if len(self.appliedOp.outParams)==0:
            return ""
        # 把outC中的结果取出
        output_names = []
        for out_param in self.appliedOp.outParams:
            output_name = f"{tmp_outC_name}.{out_param.name}"
            output_names.append(output_name)

        # 添加代码到preEquations中
        genEqu.add_preEquations(code)
        output_names=output_names[0] if len(output_names) == 1 else output_names
        if len(self.appliedOp.inParams)==0 and self.appliedOp.hasInternalState:
            if (cache := my_op.opReturnSymbolCache.get(self.appliedOp.get_outC_name())) is not None:
                if not cache[1]:
                    cache[1]=output_names
        return output_names
    def set_params(self, params: list['SyntaxExpr']):
        """代码生产环节使用，设置用于产生代码的参数表达式"""
        self.paramExprs=params
    def set_param_expr(self,param_expr):
        """初始化时使用，设置用于类型推导等环节的参数表达式"""
        self.paramExpr=param_expr
    def __init__(self, type: str, subtype: str, scope: 'SyntaxScope', objects: list or None = None, returnNum=1):
        super().__init__(type,subtype,scope,objects,returnNum)
        ...
    def get_applied_op(self):
        return self.appliedOp