#!/bin/bash

# example
# bash ./run.sh -i ./input/control_block.scade -o ./output/

green="\033[32m"
red="\033[31m"
black="\033[0m"

help()
{
    echo -e "${green}
    ----------
    command line options
    -i or --input_path
    -o or --output_dir
    ----------
    ${black}"
    exit 0;
}

ARGS=$(getopt -o i:o: -l input_path:,output_dir: -n "$0" -- "$@")

eval set -- "${ARGS}"

input_path=""
output_dir=""

while :
do
    case "$1" in
    -i | --input_path)
        input_path=$2;
        shift 2
        ;;
    -o | --output_dir)
        output_dir=$2;
        shift 2
        ;;
    -h | --help)
        help;
        shift
        ;;
    --)
        shift;
        break
        ;;
    esac
done

if [ -z "${input_path}" ] || [ -z "${output_dir}" ]; then
    help
fi

if [ ! -e "${input_path}" ]; then
    echo -e "${red} ${input_path} is not exist. ${black}"
fi

if [ ! -e "${output_dir}" ]; then
    mkdir -p ${output_dir}
fi

python3 ./scade_preprocess_stage1.py -i ${input_path} > tmp_preprocess_stage1.txt 2>&1
output_stage1=$(awk '/output_file path:/ {print $NF}' tmp_preprocess_stage1.txt)
python3 ./scade_preprocess_stage2.py -i ${output_stage1} > tmp_preprocess_stage2.txt 2>&1
output_stage2=$(awk '/output_file path:/ {print $NF}' tmp_preprocess_stage2.txt)
python3 ./scade_generate.py -i ${output_stage2} -o ${output_dir} > tmp_generate.txt 2>&1
output_dir=$(awk '/output_dir path:/ {print $NF}' tmp_generate.txt)

if ! command -v clang-format &> /dev/null; then
    sudo apt update
    sudo apt install clang-format
fi

cp ./source_program/.clang-format ${output_dir}/

files=$(find ${output_dir} -name "*.c" -o -name "*.h" -o -name "*.cpp" -o -name "*.hpp")
if [ ! -z "${files}" ]; then
    echo "${files}" | xargs clang-format -i
fi

#若生成错误。可以把这三行注释掉。看是哪个阶段错误了
rm tmp_preprocess_stage1.txt
rm tmp_preprocess_stage2.txt
rm tmp_generate.txt

rm ${output_stage1}
rm ${output_stage2}