import scade_generate as scade_generate
from syntax_tree.SyntaxClass import *
import graph


def is_nest_automaton(automaton: SyntaxAutomaton) -> bool:
    """查看此状态机是否嵌套在其他状态机内，嵌套与非嵌套的状态机生成的代码存在区别"""
    scope = automaton.prevScope
    while scope is not None:
        if scope.type == "automaton": return True
        scope = scope.prevScope
    return False


def get_automaton_state_type_name(automaton: SyntaxAutomaton) -> str:
    """状态枚举类型的定义变量名"""
    return f"SSM_ST_{get_automaton_full_name(automaton)}"


def get_automaton_transfer_type_name(automaton: SyntaxAutomaton) -> str:
    """获取状态机转移枚举类型的定义变量名"""
    return f"SSM_TR_{get_automaton_full_name(automaton)}"


def get_automaton_full_name(automaton: SyntaxAutomaton) -> str:
    """把global去了然后把：：换成_
    某个地方已经把global去掉了
    """
    return automaton.get_global_name()


def get_state_nxt(automaton: SyntaxAutomaton) -> str:
    """状态枚举类型声明的变量名，就是outC里面的变量名字,即这个周期处于激活态的状态"""
    return f"{get_automaton_full_name(automaton)}_state_nxt"


def get_state_act(automaton: SyntaxAutomaton) -> str:
    """这个状态机在这个周期所处的状态"""
    return f"{get_automaton_full_name(automaton)}_state_act"


def get_state_sel(automaton: SyntaxAutomaton) -> str:
    """嵌套状态机在此周期开始时所处的状态，若有初始化则为init状态，否则为上一周期的状态"""
    return f"{get_automaton_full_name(automaton)}_state_sel"


def get_fired_strong(automaton: SyntaxAutomaton) -> str:
    """这个状态机所经历的强转换"""
    return f"{get_automaton_full_name(automaton)}_fired_strong"


def get_state_enum_name(state: SyntaxState) -> str:
    """返回这个状态对应的枚举类型名字"""
    return f"SSM_st_{state.name}_{get_automaton_full_name(state.prevScope)}"


def get_no_trans(automaton: SyntaxAutomaton) -> str:
    """返回没有状态转移的转移枚举"""
    automaton_name = get_automaton_full_name(automaton)
    return f"SSM_TR_no_trans_{automaton_name}"


def get_trans(from_state: SyntaxState, arrow: SyntaxArrow, automaton: SyntaxAutomaton) -> str:
    """生成转移枚举"""
    return f"SSM_TR_{from_state.name}_{arrow.target}_{str(arrow.targetIndex)}_{from_state.name}_{get_automaton_full_name(automaton)}"


def get_reset_act(automaton: SyntaxAutomaton) -> str:
    """生成状态机的reset_act变量名"""
    return f"{get_automaton_full_name(automaton)}_reset_act"


def generate_expr_for_arrow_conditions(from_state, code_generator, sub_expr, depth) -> (str,str):
    """将arrow的判断部分的代码生成出来"""
    tmp_symbol, tmp_name = scade_generate.generate_tmp_symbol_and_register(from_state, SyntaxType("bool"))
    equation = SyntaxEquation(type="simple_equation", lhs=[tmp_name], lineno=-1)
    equation.set_expr(sub_expr)
    tmp_decls = f"{'    ' * depth}kcg_bool {tmp_name};\n"
    tmp_decls += scade_generate.generate_userOp_simple_equation(equation, from_state, code_generator, depth)
    return tmp_decls,tmp_name


def generate_arrow_strong(arrow: SyntaxArrow, from_state: SyntaxState, automaton: SyntaxAutomaton,
                          code_generator: scade_generate.GenerateCode, depth: int = 1) -> str:
    """给arrow生成强转移代码，可以嵌套的生成代码"""
    code = ""
    # 生成arrow中action部分的代码
    if arrow.action is not None:
        data_def_scope = from_state.get_childScope(arrow.action)
        code +=  code_generator.generate_data_def(data_def_scope, depth)
    if arrow.type != "if":
        # 这里停止递归
        target_state = automaton.get_childScope(arrow.target)
        code += f"{'    ' * depth}{get_state_act(automaton)} = {get_state_enum_name(target_state)};\n"
        code += f"{'    ' * depth}{get_fired_strong(automaton)} = {get_trans(from_state, arrow, automaton)};\n"
        if arrow.type == "resume":
            code += f"{'    ' * depth}{get_reset_act(automaton)} = kcg_false;\n"
        else:
            code += f"{'    ' * depth}{get_reset_act(automaton)} = kcg_true;\n"
        return code
    else:
        # 这里开始递归
        tmp_decls = ""  # 临时变量声明
        for i in range(len(arrow.ifExprList)):
            # 给判断表达式生成一个句子，这样即使是复杂情况也可以正确执行
            # tmp_n = 表达式
            # 然后用tmp_n代替原来的表达式参与判断
            # 要给tmp_n声明

            # todo 补全state内action中有一些赋值，需要更新返回集合，也就是处理default的情况
            sub_expr = arrow.ifExprList[i][0]
            sub_arrow = arrow.ifExprList[i][1]

            tmp_decls,tmp_name = generate_expr_for_arrow_conditions(from_state, code_generator, sub_expr, depth)

            if i == 0:
                code += f"{'    ' * depth}if({tmp_name}){{\n"
            else:
                code += f"{'    ' * depth}else if({tmp_name}){{\n"
            code += generate_arrow_strong(sub_arrow, from_state, automaton, code_generator, depth + 1)
            code += f"{'    ' * depth}}}\n"
        if arrow.elseExpr:
            code += f"{'    ' * depth}else{{\n"
            code += generate_arrow_strong(arrow.elseExpr, from_state, automaton, code_generator, depth + 1)
            code += f"{'    ' * depth}}}\n"
        code = tmp_decls + code  # 把临时变量插入
        return code


def generate_arrow_weak(arrow: SyntaxArrow, from_state: SyntaxState, automaton: SyntaxAutomaton,
                        code_generator: scade_generate.GenerateCode, depth: int = 1) -> str:
    """生成弱转移的代码，也是可以嵌套生成代码"""
    code = ""
    # 生成arrow中action部分的代码
    if arrow.action is not None:
        data_def_scope = from_state.get_childScope(arrow.action)
        code +=  code_generator.generate_data_def(data_def_scope, depth)
    if arrow.type != "if":
        # 这里停止递归
        target_state = automaton.get_childScope(arrow.target)
        code += f"{'    ' * depth}outC->{get_state_nxt(automaton)} = {get_state_enum_name(target_state)};\n"
        # 以后还会用到他们的
        # if arrow.type=="resume":
        #     code+=f"{'     * depth}{get_reset_act(automaton)} = false;\n"
        # else:
        #     code += f"{'     * depth}{get_reset_act(automaton)} = true;\n"
        return code
    else:
        # 这里开始递归
        tmp_decls = ""  # 临时变量声明
        for i in range(len(arrow.ifExprList)):
            # 给判断表达式生成一个句子，这样即使是复杂情况也可以正确执行
            # tmp_n = 表达式
            # 然后用tmp_n代替原来的表达式参与判断
            # 要给tmp_n声明

            sub_expr = arrow.ifExprList[i][0]
            sub_arrow = arrow.ifExprList[i][1]
            tmp_decl,tmp_name = generate_expr_for_arrow_conditions(from_state, code_generator, sub_expr, depth)
            tmp_decls+=tmp_decl
            if i == 0:
                code += f"{'    ' * depth}if({tmp_name}){{\n"
            else:
                code += f"{'    ' * depth}else if({tmp_name}){{\n"
            code += generate_arrow_weak(sub_arrow, from_state, automaton, code_generator, depth + 1)
            code += f"{'    ' * depth}}}\n"
        if arrow.elseExpr:
            code += f"{'    ' * depth}else{{\n"
            code += generate_arrow_weak(arrow.elseExpr, from_state, automaton, code_generator, depth + 1)
            code += f"{'    ' * depth}}}\n"
        code = tmp_decls + code  # 把临时变量插入
        return code


def generate_state_strong_transitions(automaton: SyntaxAutomaton, state: SyntaxState,
                                      code_generator: scade_generate.GenerateCode, depth: int = 1) -> str:
    """生成这个状态所对应的强转换语句
    注意到transitions和arrow的转移格式是一样的，所以这里把transtions捏成一个arrow然后进行生成会比较方便
    """
    code = ""

    tmp_arrow = SyntaxArrow(type="if", target=None, ifExpr=state.unlessTransitions, elseExpr=None)
    # 将transitions变成一个arrow处理
    # else的情况要手动添加，也就是没有转移的时候
    code += generate_arrow_strong(tmp_arrow, state, automaton, code_generator, depth)
    if len(state.unlessTransitions) != 0:
        code += f"{'    ' * (depth)}else{{\n"
        code += f"{'    ' * (depth + 1)}{get_state_act(automaton)} = {get_state_enum_name(state)};\n" \
                f"{'    ' * (depth + 1)}{get_fired_strong(automaton)} = {get_no_trans(automaton)};\n"
        code += f"{'    ' * (depth + 1)}{get_reset_act(automaton)} = kcg_false;\n"
        code += f"{'    ' * (depth)}}}\n"
    else:
        code += f"{'    ' * (depth)}{get_state_act(automaton)} = {get_state_enum_name(state)};\n" \
                f"{'    ' * (depth)}{get_fired_strong(automaton)} = {get_no_trans(automaton)};\n"
        code += f"{'    ' * (depth)}{get_reset_act(automaton)} = kcg_false;\n"

    return code


def generate_state_weak_transitions(automaton: SyntaxAutomaton, state: SyntaxState,
                                    code_generator: scade_generate.GenerateCode, depth: int = 1) -> str:
    """生成这个状态对应的弱转移语句，和强转移情况类似，捏成arrow再处理会方便一些
    注意如果是强转移来的则不能再进行弱转移了
    有弱状态restart到一个有内存的状态，则设置outC->restart_nxt,并更新之
    """

    code = ""
    # 这里要处理一下由强转移来的情况，加一层判断
    code += f"{'    ' * (depth)}if ({get_fired_strong(automaton)} != {get_no_trans(automaton)}){{\n" \
            f"{'    ' * (depth + 1)}outC->{get_state_nxt(automaton)} = {get_state_enum_name(state)};\n" \
            f"{'    ' * (depth)}}}\n" \
            f"{'    ' * (depth)}else{{\n"  # 这样把下面的代码给接上

    if len(state.untilTransitions) != 0:
        tmp_arrow = SyntaxArrow(type="if", target=None, ifExpr=state.untilTransitions, elseExpr=None)
        # 将transitions变成一个arrow处理
        # else的情况要手动添加，也就是没有转移的情况
        code += generate_arrow_weak(tmp_arrow, state, automaton, code_generator, depth + 1)
        code += f"{'    ' * (depth + 1)}else{{\n"
        # 这里是有弱转移，但是并未触发的情况
        # 需要补充上弱转移action中的赋值语句，设置default，这里应该是在第二次遍历时的工作
        code += f"{'    ' * (depth + 2)}outC->{get_state_nxt(automaton)} = {get_state_enum_name(state)};\n"
        code += f"{'    ' * (depth + 1)}}}\n"
    else:
        # 若无转移则不用处理action内部代码
        code += f"{'    ' * (depth + 1)}outC->{get_state_nxt(automaton)} = {get_state_enum_name(state)};\n"

    code += f"{'    ' * (depth)}}}\n"

    return code


def generate_body(automaton: SyntaxAutomaton, code_generator: scade_generate.GenerateCode, depth: int = 1, ) -> str:
    """生成状态机的函数体部分，在这里根据状态机是否嵌套，执行不同的函数nest和not_nest
    起到一个转发的效果"""
    if is_nest_automaton(automaton):
        return generate_body_nest(automaton, code_generator, depth)
    else:
        return generate_body_not_nest(automaton, code_generator, depth)


def generate_body_nest(automaton: SyntaxAutomaton, code_generator: scade_generate.GenerateCode,
                       depth: int = 1, ) -> str:
    """
    目前来看是将init的部分挪到这里来进行，然后在生成非嵌套的代码
    state内加入，若reset_act则outcinit为true
    然后对内存执行重置
    """
    initSymbol = automaton.prevScope.set_init_var()
    initSymbol_name=initSymbol.name
    state_enum = get_state_act(automaton)
    transfer_enum = get_fired_strong(automaton)
    decls = ""
    decls += f"{'    ' * depth}{get_automaton_state_type_name(automaton)} {state_enum};\n"
    decls += f"{'    ' * depth}{get_automaton_transfer_type_name(automaton)} {transfer_enum};\n"
    decls += f"{'    ' * depth}kcg_bool {get_reset_act(automaton)};\n"
    decls += f"{'    ' * depth}{get_automaton_state_type_name(automaton)} {get_state_sel(automaton)};\n"

    decls += f"{'    ' * depth}if (outC->{initSymbol_name}) {{\n" \
             f"{'    ' * (depth + 1)}{get_state_sel(automaton)} = {get_state_enum_name(automaton.get_init_state())};\n" \
             f"{'    ' * depth}}}\n" \
             f"{'    ' * depth}else{{\n" \
             f"{'    ' * (depth + 1)}{get_state_sel(automaton)} = outC->{get_state_nxt(automaton)};\n" \
             f"{'    ' * depth}}}\n"
    switch_state = f"{'    ' * depth}switch ({get_state_sel(automaton)}){{\n"
    switch_state += generate_switch_state_body(automaton, code_generator, depth)
    switch_act = generate_switch_act(automaton, code_generator, depth)
    return decls + switch_state + switch_act


def generate_body_not_nest(automaton: SyntaxAutomaton, code_generator: scade_generate.GenerateCode,
                           depth: int = 1, ) -> str:
    """
    生成对应的函数体部分
    先是强迁移unless部分
    然后执行state内语句
    然后弱迁移until
    """
    state_enum = get_state_act(automaton)
    transfer_enum = get_fired_strong(automaton)
    decls = ""
    decls += f"{'    ' * depth}{get_automaton_state_type_name(automaton)} {state_enum};\n"
    decls += f"{'    ' * depth}{get_automaton_transfer_type_name(automaton)} {transfer_enum};\n"
    decls += f"{'    ' * depth}kcg_bool {get_reset_act(automaton)};\n"
    # 临时的变量声明

    # 生成状态和转移枚举部分，然后开始强迁移部分的代码生成
    switch_state = f"{'    ' * depth}switch (outC->{get_state_nxt(automaton)}){{\n"  # 状态枚举，做强转移，处理reset_nxt（如果有）
    switch_state += generate_switch_state_body(automaton, code_generator, depth)
    switch_act = generate_switch_act(automaton, code_generator, depth)

    code = decls + switch_state + switch_act
    return code


def generate_switch_state_body(automaton: SyntaxAutomaton, code_generator: scade_generate.GenerateCode, depth) -> str:
    """生成状态机body中，强转移部分的主体部分，此部分对嵌套与非嵌套的状态机逻辑是一样的"""
    body = ""
    for state_name, state in automaton.stateTable.items():
        body += f"{'    ' * (depth + 1)}case {get_state_enum_name(state)}: {{\n"
        body += generate_state_strong_transitions(automaton, state, code_generator, depth + 2)
        body += f"{'    ' * (depth + 2)}break;}}\n"
    body += f"{'    ' * (depth + 1)}default:break;\n{'    ' * depth}}}\n"
    return body


def generate_switch_act(automaton: SyntaxAutomaton, code_generator: scade_generate.GenerateCode, depth) -> str:
    """生成状态机body中，状态内代码执行和弱转移部分的全部，此部分对嵌套与非嵌套的状态机逻辑是一样的"""
    # 行动枚举，执行当前状态下的代码，然后做弱转移
    switch_act = f"{'    ' * (depth)}switch ({get_state_act(automaton)}){{\n"
    for state_name, state in automaton.stateTable.items():
        data_def_code= code_generator.generate_data_def(state, depth + 2)
        switch_act += f"{'    ' * (depth + 1)}case {get_state_enum_name(state)}:{{\n"

        if state.hasInternalState or\
            any([applied_expr.appliedOp.hasInternalState for applied_expr in state.apply_exprs]):
            # 如果此状态有内存，则加上一个重置操作,即如果rest_act，则设置init为true，然后重置操作，然后将init为false
            switch_act += f"{'    ' * (depth + 2)}if({get_reset_act(automaton)}){{\n"

            for applied_expr in state.apply_exprs:
                if not applied_expr.appliedOp.hasInternalState: continue
                depth = 1
                # todo 调用函数情况为数组的reset过程，参考array初始化
                switch_act += f"{'    ' * (depth + 3)}{applied_expr.appliedOp.get_global_name()}_reset(&(outC->{applied_expr.appliedOpOutCName}));\n"

            for initSymbol in state.initSymbolSet:
                switch_act += f"{'    ' * (depth + 3)}outC->{initSymbol.name} = kcg_true;\n"
            if state.initVar:
                switch_act += f"{'    ' * (depth + 3)}outC->{state.initVar.name} = kcg_true;\n"
            switch_act += f"{'    ' * (depth + 2)}}}\n"
            # 这里接如果为init则进行的初始化操作

        # 这里添加代码，调用data_def的代码生成逻辑
        switch_act += data_def_code
        # 然后是弱转移部分
        switch_act += generate_state_weak_transitions(automaton, state, code_generator, depth + 2)
        if state.hasInternalState:
            for initSymbol in state.initSymbolSet:
                switch_act += f"{'    ' * (depth + 2)}outC->{initSymbol.name} = kcg_false;\n"
            switch_act += f"{'    ' * (depth + 2)}outC->{state.initVar.name} = kcg_false;\n"
            # 然后初始化结束
        switch_act += f"{'    ' * (depth + 2)}break;}}\n"
    switch_act += f"{'    ' * (depth + 1)}default:break;\n{'    ' * depth}}}\n"
    return switch_act


def generate_state_nxt_for_head(automaton: SyntaxAutomaton) -> str:
    """生成头文件，记录状态机的下一个状态"""
    code = f"    {get_automaton_state_type_name(automaton)}    {get_state_nxt(automaton)};\n"
    return code



def generate_state_nxt_for_init(automaton: SyntaxAutomaton) -> str:
    """生成对应的init函数
    只有第一层的状态机有它的init函数，嵌套的情况则不一样
    初始化最外层状态机的state_nxt
    """
    code = f"    outC->{get_state_nxt(automaton)} = {get_state_enum_name(automaton.get_init_state())};\n"

    return code


def generate_type(automaton: SyntaxAutomaton) -> str:
    """生成相关的类型定义
    有状态枚举类型ST和转移枚举类型TR两种
    转移枚举类元素的格式是SSM_TR_原来状态_新状态_序号_原来状态_状态机名字
    """
    automaton_name = get_automaton_full_name(automaton)
    transfer_enum = f"typedef enum kcg_tag_SSM_TR_{automaton_name} {{\n"
    transfer_enum += f"    {get_no_trans(automaton)},\n"

    for state_name, state in automaton.stateTable.items():
        arrow_list = state.get_strong_transfer_arrows()
        transfer_count = 1
        for arrow in arrow_list:
            transfer_enum += f"    {get_trans(state, arrow, automaton)},\n"
            transfer_count += 1
    transfer_enum = transfer_enum[:-2] + "\n} " + get_automaton_transfer_type_name(automaton) + ";\n"
    state_enum = f"typedef enum kcg_tag_SSM_ST_{automaton_name} {{\n"
    for name, state in automaton.stateTable.items():
        state_enum += f"    {get_state_enum_name(state)},\n"
    state_enum = state_enum[:-2] + "\n}  " + get_automaton_state_type_name(automaton) + ";\n"
    return transfer_enum + state_enum
