import scade_generate as scade_generate
from syntax_tree.SyntaxClass import *


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
    return '_'.join(automaton.get_global_name().split('::'))


def get_state_nxt(automaton: SyntaxAutomaton) -> str:
    """状态枚举类型声明的变量名，就是outc里面的变量名字,即这个周期处于激活态的状态"""
    return f"{get_automaton_full_name(automaton)}_state_nxt"


def get_state_act(automaton: SyntaxAutomaton) -> str:
    """这个状态机在这个周期所处的状态"""
    return f"{get_automaton_full_name(automaton)}_state_act"


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

def get_reset_act(automaton:SyntaxAutomaton)->str:
    """生成状态机的reset_act变量名"""
    return f"{get_automaton_full_name(automaton)}_reset_act"

def generate_arrow_strong(arrow: SyntaxArrow, from_state: SyntaxState, automaton: SyntaxAutomaton, depth: int = 1) -> str:
    """给arrow生成强转移代码，可以嵌套的生成代码"""
    code = ""

    if arrow.type != "if":
        # 这里停止递归
        target_state = automaton.get_childScope(arrow.target)
        code += f"{'   ' * depth}{get_state_act(automaton)} = {get_state_enum_name(target_state)};\n"
        code += f"{'   ' * depth}{get_fired_strong(automaton)} = {get_trans(from_state, arrow, automaton)};\n"
        if arrow.type=="resume":
            code+=f"{'   ' * depth}{get_reset_act(automaton)} = false;\n"
        else:
            code += f"{'   ' * depth}{get_reset_act(automaton)} = true;\n"
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

            tmp_name = from_state.generate_name_for_tmp()
            tmp_symbol = SyntaxVariableSymbol(name=tmp_name, isProbe=False, isClock=False)
            tmp_symbol.syntaxType = SyntaxType(type="bool")
            from_state.add_localSymbols([tmp_symbol])
            equation = SyntaxEquation(type="simple_equation", lhs=[tmp_name], lineno=-1)
            equation.set_expr(sub_expr)

            equation_code=scade_generate.SyntaxExpr_generate(sub_expr, from_state, equation)
            tmp_decls += f"{'   ' * depth}kcg_bool {tmp_name} = {equation_code};\n"

            if i == 0:
                code += f"{'   ' * depth}if({tmp_name}){{\n"
            else:
                code += f"{'   ' * depth}else if({tmp_name}){{\n"
            code += generate_arrow_strong(sub_arrow, from_state, automaton, depth + 1)
            code += f"{'   ' * depth}}}\n"
        if arrow.elseExpr:
            code+=f"{'   ' * depth}else{{\n"
            code += generate_arrow_strong(arrow.elseExpr, from_state, automaton, depth + 1)
            code += f"{'   ' * depth}}}\n"
        code = tmp_decls + code  # 把临时变量插入
        return code

def generate_arrow_weak(arrow: SyntaxArrow, from_state: SyntaxState, automaton: SyntaxAutomaton, depth: int = 1)->str:
    """生成弱转移的代码，也是可以嵌套生成代码"""
    code = ""

    if arrow.type != "if":
        # 这里停止递归
        target_state = automaton.get_childScope(arrow.target)
        code += f"{'   ' * depth}outc->{get_state_nxt(automaton)} = {get_state_enum_name(target_state)};\n"
        #以后还会用到他们的
        # if arrow.type=="resume":
        #     code+=f"{'   ' * depth}{get_reset_act(automaton)} = false;\n"
        # else:
        #     code += f"{'   ' * depth}{get_reset_act(automaton)} = true;\n"
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

            tmp_name = from_state.generate_name_for_tmp()
            tmp_symbol = SyntaxVariableSymbol(name=tmp_name, isProbe=False, isClock=False)
            tmp_symbol.syntaxType = SyntaxType(type="bool")
            from_state.add_localSymbols([tmp_symbol])
            equation = SyntaxEquation(type="simple_equation", lhs=[tmp_name], lineno=-1)
            equation.set_expr(sub_expr)

            equation_code=scade_generate.SyntaxExpr_generate(sub_expr, from_state, equation)
            tmp_decls += f"{'   ' * depth}kcg_bool {tmp_name} = {equation_code};\n"

            if i == 0:
                code += f"{'   ' * depth}if({tmp_name}){{\n"
            else:
                code += f"{'   ' * depth}else if({tmp_name}){{\n"
            code += generate_arrow_weak(sub_arrow, from_state, automaton, depth + 1)
            code += f"{'   ' * depth}}}\n"
        if arrow.elseExpr:
            code+=f"{'   ' * depth}else{{\n"
            code += generate_arrow_weak(arrow.elseExpr, from_state, automaton, depth + 1)
            code += f"{'   ' * depth}}}\n"
        code = tmp_decls + code  # 把临时变量插入
        return code

def generate_state_strong_transitions(automaton: SyntaxAutomaton, state: SyntaxState, depth: int = 1) -> str:
    """生成这个状态所对应的强转换语句
    注意到transitions和arrow的转移格式是一样的，所以这里把transtions捏成一个arrow然后进行生成会比较方便
    """
    code = ""

    tmp_arrow = SyntaxArrow(type="if", target=None, ifExpr=state.unlessTransitions, elseExpr=None)
    #将transitions变成一个arrow处理
    #else的情况要手动添加
    code+=generate_arrow_strong(tmp_arrow, state, automaton, depth)
    if len(state.unlessTransitions) != 0:
        code += f"{'   ' * (depth)}else{{\n"
        code += f"{'   ' * (depth + 1)}{get_state_act(automaton)} = {get_state_enum_name(state)};\n" \
                f"{'   ' * (depth + 1)}{get_fired_strong(automaton)} = {get_no_trans(automaton)};\n"
        code += f"{'   ' * (depth + 1)}{get_reset_act(automaton)} = false;\n"
        code += f"{'   ' * (depth)}}}\n"
    else:
        code += f"{'   ' * (depth)}{get_state_act(automaton)} = {get_state_enum_name(state)};\n" \
                f"{'   ' * (depth)}{get_fired_strong(automaton)} = {get_no_trans(automaton)};\n"
        code += f"{'   ' * (depth)}{get_reset_act(automaton)} = false;\n"

    return code


def generate_state_weak_transitions(automaton: SyntaxAutomaton, state: SyntaxState, depth: int = 1) -> str:
    """生成这个状态对应的弱转移语句，和强转移情况类似，捏成arrow再处理会方便一些
    注意如果是强转移来的则不能再进行弱转移了
    """

    code = ""
    #这里要处理一下由强转移来的情况，加一层判断
    code+=f"{'   ' * (depth)}if ({get_fired_strong(automaton)} != {get_no_trans(automaton)}){{\n" \
          f"{'   ' * (depth+1)}outc->{get_state_nxt(automaton)} = {get_state_enum_name(state)};\n" \
          f"{'   ' * (depth)}}}\n" \
          f"{'   ' * (depth)}else{{\n"#这样把下面的代码给接上

    if len(state.untilTransitions) != 0:
        tmp_arrow = SyntaxArrow(type="if", target=None, ifExpr=state.untilTransitions, elseExpr=None)
        # 将transitions变成一个arrow处理
        # else的情况要手动添加
        code += generate_arrow_weak(tmp_arrow, state, automaton, depth+1)
        code += f"{'   ' * (depth+1)}else{{\n"
        code += f"{'   ' * (depth + 2)}outc->{get_state_nxt(automaton)} = {get_state_enum_name(state)};\n"
        code += f"{'   ' * (depth+1)}}}\n"
    else:
        code += f"{'   ' * (depth+1)}outc->{get_state_nxt(automaton)} = {get_state_enum_name(state)};\n"

    code+=f"{'   ' * (depth)}}}\n"




    return code


def generate_body(automaton: SyntaxAutomaton, depth: int = 1) -> str:
    """生成对应的函数体部分
    先是强迁移unless部分
    然后执行state内语句
    然后弱迁移until
    """
    state_enum = get_state_act(automaton)
    transfer_enum = get_fired_strong(automaton)
    decls = ""
    decls += f"{get_automaton_state_type_name(automaton)} {state_enum};\n"
    decls += f"{get_automaton_transfer_type_name(automaton)} {transfer_enum};\n"
    decls += f"kcg_bool {get_reset_act(automaton)};\n"
    #临时的变量声明

    # 生成状态和转移枚举部分，然后开始强迁移部分的代码生成
    switch_state = f"switch (outc->{get_state_nxt(automaton)}){{\n"  # 状态枚举，做强转移，处理reset_nxt（如果有）
    for state_name, state in automaton.stateTable.items():
        switch_state += f"{'   ' * depth}case {get_state_enum_name(state)}:\n"
        switch_state += generate_state_strong_transitions(automaton, state, depth + 1)
        switch_state += f"{'   ' * (depth + 1)}break;\n"
    switch_state += "   default:break;\n}\n"


    # 行动枚举，执行当前状态下的代码，然后做弱转移
    switch_act = f"switch (outc->{get_state_act(automaton)}){{\n"
    for state_name, state in automaton.stateTable.items():
        switch_act += f"{'   ' * depth}case {get_state_enum_name(state)}:\n"

        switch_act += generate_state_weak_transitions(automaton, state, depth + 1)
        switch_act += f"{'   ' * (depth + 1)}break;\n"
    switch_act += "   default:break;\n}\n"


    code = decls + switch_state + switch_act
    return code


def generate_init(automaton: SyntaxAutomaton) -> str:
    """生成对应的init函数
    只有第一层的状态机有它的init函数，嵌套的情况则不一样
    """
    return f"outc->{get_automaton_state_type_name(automaton)} = {get_state_enum_name(automaton.get_init_state())};"


def generate_reset(automaton: SyntaxAutomaton) -> str:
    """生成对应的reset函数
    只有第一层的状态机有它的rest函数，嵌套的情况则不一样
    """
    return f"outc->{get_automaton_state_type_name(automaton)} = {get_state_enum_name(automaton.get_init_state())};"


def generate_head(automaton: SyntaxAutomaton) -> str:
    """生成头文件中的local memories"""
    return f"{get_automaton_state_type_name(automaton)}    {get_state_nxt(automaton)};\n"


def generate_type(automaton: SyntaxAutomaton) -> str:
    """生成相关的类型定义
    有状态枚举类型ST和转移枚举类型TR两种
    转移枚举类元素的格式是SSM_TR_原来状态_新状态_序号_原来状态_状态机名字
    """
    automaton_name = get_automaton_full_name(automaton)
    transfer_enum = f"typedef enum kcg_tag_SSM_TR_{automaton_name} {{\n"
    transfer_enum += f"   {get_no_trans(automaton)},\n"

    for state_name, state in automaton.stateTable.items():
        arrow_list = state.get_strong_transfer_arrows()
        transfer_count = 1
        for arrow in arrow_list:
            transfer_enum += f"   {get_trans(state, arrow, automaton)},\n"
            transfer_count += 1
    transfer_enum = transfer_enum[:-2] + "\n} " + get_automaton_transfer_type_name(automaton) + "\n"
    state_enum = f"typedef enum kcg_tag_SSM_ST_{automaton_name} {{\n"
    for name, state in automaton.stateTable.items():
        state_enum += f"   {get_state_enum_name(state)},\n"
    state_enum = state_enum[:-2] + "\n}  " + get_automaton_state_type_name(automaton) + "\n"
    return transfer_enum + state_enum
