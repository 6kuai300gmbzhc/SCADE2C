import scade_generate as scade_generate
from SyntaxClass import *

def get_automaton_state_type_name(automaton: SyntaxAutomaton)->str:
    """状态枚举类型的定义变量名"""
    return f"SSM_ST_{get_automaton_full_name(automaton)}"
def get_automaton_transfer_type_name(automaton: SyntaxAutomaton)->str:
    """获取状态机转移枚举类型的定义变量名"""
    return f"SSM_TR_{get_automaton_full_name(automaton)}"
def get_automaton_full_name(automaton: SyntaxAutomaton)->str:
    """把global去了然后把：：换成_"""
    return '_'.join(automaton.get_global_name().split('::')[1:])
def get_automaton_state_var_name(automaton: SyntaxAutomaton)->str:
    """状态枚举类型声明的变量名，就是outc里面的变量名字"""
    return f"{get_automaton_full_name(automaton)}_state_nxt"
def get_state_act(automaton:SyntaxAutomaton)->str:
    """这个状态机在这个周期所处的状态"""
    return f"{get_automaton_full_name(automaton)}_state_act"
def get_fired_strong(automaton:SyntaxAutomaton)->str:
    """这个状态机所经历的强转换"""
    return f"{get_automaton_full_name(automaton)}_fired_strong"
def get_state_enum_name(state:SyntaxState)->str:
    """返回这个状态对应的枚举类型名字"""
    return f"SSM_st_{state.name}_{get_automaton_full_name(state.prevScope)}"
def get_no_trans(automaton:SyntaxAutomaton)->str:
    """返回没有状态转移的转移枚举"""
    automaton_name=get_automaton_full_name(automaton)
    return f"SSM_TR_no_trans_{automaton_name}"
def get_trans():pass

def generate_state_strong_transitions(automaton:SyntaxAutomaton,state:SyntaxState)->str:
    """生成这个状态所对应的强转换语句"""
    pass
    code=""
    # for i in range(len(state.unlessTransitions)):
    #     expr=state.unlessTransitions[i][0]
    #     arrow=state.unlessTransitions[i][1]
    #     if i==0:
    #         code+=f"   if({}){{\n"
    #     else:code+=f"   else if({}){{\n"
    #
    #
    #     code+="}\n"
    # code+=f"else{{\n      {get_state_act(automaton)} = {get_state_enum_name(state)};\n" \
    #       f"      {get_fired_strong(automaton)} = {}" \
    #       f"}}\n"
    return code



def generate_body(automaton: SyntaxAutomaton) -> str:
    """生成对应的函数体部分
    先是强迁移unless部分
    然后执行state内语句
    然后弱迁移until
    """
    state_enum = get_state_act(automaton)
    transfer_enum = get_fired_strong(automaton)
    decls=""
    decls+=f"{get_automaton_state_type_name(automaton)} {state_enum};\n"
    decls+=f"{get_automaton_transfer_type_name(automaton)} {transfer_enum};\n"
    #生成状态和转移枚举部分，然后开始强迁移部分的代码生成


    switch_state=f"switch (outc->{get_automaton_state_var_name(automaton)}){{\n"#状态枚举，做强转移，处理reset_nxt（如果有）
    for state_name, state in automaton.stateTable.items():
        switch_state+=f"   case {get_state_enum_name(state)}:\n"

        switch_state+="      break;\n"
    switch_state+="   default:break;\n}\n"
    switch_act=""#行动枚举，执行当前状态下的代码，然后做弱转移

    code=decls+switch_state+switch_act
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
    return f"{get_automaton_state_type_name(automaton)}    {get_automaton_state_var_name(automaton)};\n"


def generate_type(automaton: SyntaxAutomaton) -> str:
    """生成相关的类型定义
    有状态枚举类型ST和转移枚举类型TR两种
    转移枚举类元素的格式是SSM_TR_原来状态_新状态_序号_原来状态_状态机名字
    """
    automaton_name = get_automaton_full_name(automaton)
    transfer_enum = f"typedef enum kcg_tag_SSM_TR_{automaton_name} {{\n"
    transfer_enum+=f"   {get_no_trans(automaton)},\n"

    for state_name,state in automaton.stateTable.items():
        target_list=state.get_transfer_target_names()
        transfer_count = 1
        for target_name in target_list:
            transfer_enum+=f"   SSM_TR_{state_name}_{target_name}_{str(transfer_count)}_{state_name}_{automaton_name},\n"
            transfer_count+=1
    transfer_enum = transfer_enum[:-2]+"\n} "+get_automaton_transfer_type_name(automaton)+"\n"
    state_enum = f"typedef enum kcg_tag_SSM_ST_{automaton_name} {{\n"
    for name, state in automaton.stateTable.items():
        state_enum += f"   {get_state_enum_name(state)},\n"
    state_enum = state_enum[:-2] + "\n}  " + get_automaton_state_type_name(automaton) + "\n"
    return transfer_enum+state_enum
