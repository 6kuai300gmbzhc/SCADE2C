import argparse
from .scade_preprocess import get_parse
from .scade_postprocess import post_process
from .scade_type_inference import type_inference
from .scade_generate import generate

def get_final_order(order):
    final_order=list()
    for op in order:
        if op.isTemplate() and not op.instantiatedOpList:
            raise Exception(f"{op.get_global_name()}是模板函数但是没有实例化")
        if not op.instantiatedOpList:
            final_order.append(op)
        else:
            final_order.extend(op.instantiatedOpList)
    return final_order
def scade_parse(input_path: str, main_operator_path: str, output_path: str, need_test_file: bool):
    root_scope=get_parse(input_path, main_operator_path)
    post_order,main_operator=post_process(root_scope, main_operator_path)
    # 后处理流程，在这里进行拓扑排序
    instantiated_op_order=type_inference(main_operator) # 主节点在最后一个，是必然的,即进行一个反向的遍历
    # 类型推导流程，进行类型校验，模板函数实例化等问题，会对语法树进行更新
    order=get_final_order(post_order)
    print("最终进行代码生成的op:")
    print([op for op in order])
    print("有最终的遍历顺序为:")
    print([op.get_global_name() for op in order])

    generate(main_operator_path, root_scope, order, output_path, need_test_file)
def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-i', '--input_path', required=True, type=str)
    argParser.add_argument('-m', '--main_operator', required=True, type=str)
    argParser.add_argument('-o', '--output_path', required=True, type=str)
    argParser.add_argument('-t', '--need_test_file', required=False, action="store_true",default=False)
    args = argParser.parse_args()
    scade_parse(args.input_path, args.main_operator, args.output_path, args.need_test_file)
if __name__ == '__main__':
    main()