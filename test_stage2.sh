#!/bin/bash
# for test stage2
# FILES=$(find ./input -name "*.scade")
# for file in ${FILES}; do
#     name=$(basename ${file} .scade)
#     echo "Process file ${name}"
#     python scade_preprocess_stage2.py -i ./.ignore_this/stage1/stage1_${name}.scade > stage2_${name}.log  2>&1
#     if tail -n 1 stage2_${name}.log | grep -q "output_file path:"; then
#         :
#     else
#         echo "Fail"
#     fi
# done

# for test stage1
# FILES=$(find ./input -name "*.scade")
# for file in ${FILES}; do
#     name=$(basename ${file} .scade)
#     echo "Process file ${name}"
#     python scade_preprocess_stage1.py -i ${file} > stage1_${name}.scade > stage1_${name}.log 2>&1
#     if tail -n 1 stage1_${name}.log | grep -q "output_file path:"; then
#         :
#     else
#         echo "Fail"
#     fi
# done

#for test stage1 && stage2
FILES=$(find ./.ignore_this/input/ -name "*.scade")
for file in ${FILES}; do
    name=$(basename ${file} .scade)
    python scade_preprocess_stage1.py -i ${file} > stage1_${name}.scade > stage1_${name}.log 2>&1
    if tail -n 1 stage1_${name}.log | grep -q "output_file path:"; then
        python scade_preprocess_stage2.py -i stage1_${name}.scade > stage2_${name}.log 2>&1
        if tail -n 1 stage2_${name}.log | grep -q "output_file path:"; then
            :
        else
            echo "Fail"
    fi
    else
        echo "Fail"
    fi
done