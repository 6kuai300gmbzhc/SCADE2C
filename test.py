import os
import subprocess
import glob
import logging

open('log.txt', 'w').close()

# 设置 logging，输出到 log.txt 文件
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

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
        
        # 构建命令行：python scade_generate.py -i ./input/file.txt -o ./output
        command = ['python', 'scade_generate.py', '-i', input_file, '-o', output_dir]

        try:
            # 使用 subprocess 调用外部命令行，不进行解码，直接处理原始的字节数据
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 只将成功信息记录到日志文件
            logging.info(f"Success processing file: {filename}")
        
        except subprocess.CalledProcessError as e:
            # 捕捉并记录错误信息到日志文件
            logging.error(f"Error processing file: {filename}")
            logging.error(f"Error message: {e.stderr.decode(errors='ignore')}")
            continue  # 跳过出错的文件

if __name__ == '__main__':
    # 定义输入和输出路径
    input_dir = './input'
    output_dir = './output'
    
    # 调用测试函数
    test_scade_generate(input_dir, output_dir)
