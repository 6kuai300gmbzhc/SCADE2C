import random
import os

from syntax_tree.syntax_class.syntaxType import SyntaxType


def generate_random_data(syntax_type:SyntaxType):
    """生成两份测试数据"""
    def generate_for_base_type(base_type:SyntaxType):
        type_str=base_type.type
        if type_str in SyntaxType.hierarchy_dict['float']:
            data = format(random.random() * 100, ".2f")
        elif type_str == "bool":
            data = "true" if random.random() > 0.5 else "false"
        elif (type_str in SyntaxType.hierarchy_dict['signed'] and type_str!='signed') or \
                (type_str in SyntaxType.hierarchy_dict['unsigned'] and type_str!='unsigned'):
            data = str(int(random.random() * 5))
        else:
            raise Exception(base_type.__repr__()+"不是基础类型")
        return data
    syntax_type=syntax_type.get_real_type()
    if syntax_type.is_basic_type():
        base_data=generate_for_base_type(syntax_type)
        test_data=base_data
        c_data=base_data
    elif syntax_type.type=="array":
        size=syntax_type.get_size()
        element_type=syntax_type.get_element_type_for_array()
        test_data=""
        c_data=""
        for i in range(size):
            ele_test,ele_c=generate_random_data(element_type)
            test_data+=ele_test+" "
            c_data+=ele_c+","
        c_data=f"{{{c_data[:-1]}}}"
    elif syntax_type.type=="field_decl":
        test_data=""
        c_data=""
        for sub_symbol in syntax_type.fields:
            ele_test, ele_c = generate_random_data(sub_symbol.syntaxType)
            test_data+=ele_test+" "
            c_data+=ele_c+","
        c_data=f"{{{c_data[:-1]}}}"
    elif syntax_type.type=="enum":
        # 输出一个整数
        random_num=str(random.randrange(0, len(syntax_type.enumList)))
        c_data=random_num
        test_data=random_num
    else:
        raise Exception("还没写")
    return test_data,c_data


def check_file_status(file_path):
    """
    判断文件是否存在以及是否为空
    :param file_path: 文件路径
    :return: 存在且非空返回 True, 不存在或为空返回 False
    """
    if not os.path.exists(file_path):
        return False
    if os.path.getsize(file_path) == 0:
        return False
    return True
def generate(input_types:list[SyntaxType],name,data_num,outputDir):
    scade_file_path=f"{outputDir}/test_data_{name}_scade.in"
    c_file_path=f"{outputDir}/test_data_{name}_c.txt"
    if check_file_status(c_file_path) and check_file_status(scade_file_path):
        return
    scade_out=""
    c_out:list[list[str]]=[[] for i in range(len(input_types))]
    for i in range(data_num):
        for c,_type in enumerate(input_types):
            if i==0 and _type.type=="bool":
                test_data, c_data=("true","true")
            else:
                test_data,c_data=generate_random_data(_type)
            scade_out += test_data + " "
            c_out[c].append(c_data)
        scade_out+="\n"
    with open(scade_file_path,"w") as test_data:
        test_data.write(scade_out)
    with open(c_file_path, "w") as c_data:
        c_data.write("\n".join([",".join([c_out[i][j] for j in range(len(c_out[i]))]) for i in range(len(c_out))]))
if __name__ == "__main__":

    print(generate_random_data(SyntaxType("int32")))


    arr_type=SyntaxType("array",scope='test')
    arr_type.set_element_and_size(SyntaxType("int32"),4)
    print(generate_random_data(arr_type))
    # generate([SyntaxType("int32"),SyntaxType("bool")],"DisplayLogic",100,".")