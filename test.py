import os
import subprocess
import glob
import logging
from scade_generate import testInputFile
from scade_preprocess_stage1 import get_parse as stage1_get_parse
from scade_preprocess_stage2 import get_parse as stage2_get_parse

open('log.txt', 'w').close()

# 设置 logging，输出到 log.txt 文件
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def format_code_with_clang_format(file_path: str):
    """调用 clang-format 格式化 C++ 代码，使用文件风格"""
    command = ['clang-format', '--style=file', '-i', file_path]  # 使用 --style=file
    try:
        subprocess.run(command, check=True)
        logging.info(f"Formatted file: {file_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to format file: {file_path}")
        logging.error(f"Error message: {str(e)}")

def format_all_cpp_files_in_directory(directory: str):
    """格式化指定目录下所有 C/C++ 相关文件"""
    file_patterns = ['*.c', '*.h', '*.cpp', '*.hpp']
    
    for pattern in file_patterns:
        # 使用 glob 找到所有匹配的文件
        for file_path in glob.glob(os.path.join(directory, '**', pattern), recursive=True):
            format_code_with_clang_format(file_path)

def preprocess(input_file: str, output_dir: str):
    """执行预处理步骤并生成最终文件"""
    try:
        # 第一阶段预处理
        stage1_output_file = f"stage1_{os.path.splitext(os.path.basename(input_file))[0]}.scade"
        stage1_output_path = os.path.join(output_dir, stage1_output_file)
        stage1_get_parse(input_file)
        logging.info(f"Stage 1 processed file: {stage1_output_file}")

        try:
            # 第二阶段预处理
            stage2_output_file = f"stage2_{stage1_output_file}"
            stage2_output_path = os.path.join(output_dir, stage2_output_file)
            stage2_get_parse(stage1_output_path)
            logging.info(f"Stage 2 processed file: {stage2_output_file}")

            return stage1_output_path, stage2_output_path  # 返回两个阶段的输出文件路径

        except Exception as e:
            logging.error(f"Error in stage 2 processing for file: {stage1_output_file}")
            logging.error(f"Error message: {str(e)}")
            logging.error("Traceback:", exc_info=True)
            return stage1_output_path, None

    except Exception as e:
        logging.error(f"Error in stage 1 processing for file: {input_file}")
        logging.error(f"Error message: {str(e)}")
        logging.error("Traceback:", exc_info=True)
        return None, None

def test_scade_generate(input_dir: str, output_dir: str):
    # 检查输出目录是否存在，如果不存在则创建
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取 ./input 目录下的所有文件
    input_files = glob.glob(os.path.join(input_dir, '*'))
    
    # 遍历每个文件并执行命令
    for index, input_file in enumerate(input_files):
        # 检查是否为文件，跳过目录
        if not os.path.isfile(input_file):
            continue
        
        # 提取文件名
        filename = os.path.basename(input_file)
        
        # 记录文件开始处理，添加序号
        logging.info(f"Processing file {index + 1}: {filename}")
        
        # 执行预处理并生成最终文件
        stage1_output_path, stage2_output_path = preprocess(input_file, "./")
        
        if stage2_output_path:
            try:
                # 调用生成函数，输入为第二阶段的输出文件
                testInputFile(stage2_output_path, output_dir)

                # 记录成功信息
                logging.info(f"Successfully generated file: {filename}")

                # 删除中间生成的文件
                if os.path.exists(stage1_output_path):
                    os.remove(stage1_output_path)
                    logging.info(f"Deleted intermediate file: {stage1_output_path}")

                if os.path.exists(stage2_output_path):
                    os.remove(stage2_output_path)
                    logging.info(f"Deleted intermediate file: {stage2_output_path}")

            except Exception as e:
                logging.error(f"Error during generation for file: {stage2_output_path}")
                logging.error(f"Error message: {str(e)}")
                logging.info(f"\n================================================== Next Input File ===========================================================")
                continue  # 继续处理下一个文件
        else:
            logging.error(f"Skipping generation for file: {input_file} due to preprocessing errors.")
        logging.info(f"\n================================================== Next Input File ===========================================================")
    
    # 格式化输出目录下所有 C/C++ 文件
    format_all_cpp_files_in_directory(output_dir)
    
if __name__ == '__main__':
    # 定义输入和输出路径
    input_dir = './input'
    output_dir = './output'
    
    # 调用测试函数
    test_scade_generate(input_dir, output_dir)
