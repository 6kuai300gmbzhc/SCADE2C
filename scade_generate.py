import os
import scade_compile as sc
from queue import Queue
from scade_compile_otherFunc import GlobalEnv
from SymbolClass import SymbolTable
import argparse

def gen_struct_elem(elem):
    str=""
    if elem.Type=='struct':
        str+="struct {\n"
        for elemK,elemV in elem.FieldList.items():
            str+=gen_struct_elem(elemV)
        str+="}%s%s;\n"%(elem.Name,sc.getArrSize(elem.arrSize))
    else:
        str+="%s %s%s;\n"%(sc.type_change(elem.Type),elem.Name,sc.getArrSize(elem.arrSize))
    return str


class Scade_generate:
    def __init__(self,program=None,symboltable=None,ctx_table=None):
        self.program=program
        self.symboltable=symboltable
        self.ctx_table=ctx_table

        self.header_code=''
        self.main_code=''

    #此时没有考虑包的因素
    def gen_const_file(self):
        h_content = "#ifndef _KCG_CONSTS_H_\n#define _KCG_CONSTS_H_\n#include \"kcg_types.h\"\n\n"
        c_content = "#include \"kcg_consts.h\"\n"
        temp = self.symboltable
        que = Queue()
        que.put(temp)
        while not que.empty(): # 广搜，处理存在包的情况下，符号表层层嵌套的情况
            temp = que.get()
            for k,v in temp.SymbolTable.items():
                if v.Kind=="Const":
                    h_content += "extern const %s %s%s;\n"%(sc.type_change(v.Type),k+v.PackageName,sc.getArrSize(v.arrSize))
                    if v.External !=True:
                        c_content += "const %s %s%s = %s;\n"%(sc.type_change(v.Type),k + v.PackageName,sc.getArrSize(v.arrSize),sc.objectsToString(v.Code,temp))
            for table in temp.ChildTableList:
                que.put(table)
        h_content+="\n\n#endif"
        print("====const h_file")
        print(h_content)
        print("====const c_file")
        print(c_content)
        with open("%s/include/kcg_consts.h"%(sc.outputDir),'w') as f:
            f.write(h_content)
        with open("%s/src/kcg_consts.c"%(sc.outputDir),'w') as f:
            f.write(c_content)    

    def gen_sensor_file(self):
        content="#ifndef _KCG_SENSORS_H_\n#define _KCG_SENSORS_H_\n#include \"kcg_types.h\"\n\n"
        for k, v in self.symboltable.SymbolTable.items():
            if v.Kind=="Sensor":
                content+="extern %s %s%s;\n"%(sc.type_change(v.Type),k,sc.getArrSize(v.arrSize))
        content+="\n#endif"
        print("====sensor")
        print(content)
        with open('%s/include/kcg_sensors.h'%(sc.outputDir),'w') as f:
            f.write(content)

    def gen_types_file(self):
        file=open('source_program/types.txt','r')
        content=file.read()
        content+="\n"
        typeContent=""
        symbolTable=GlobalEnv
        for k,v in symbolTable.SymbolTable.items():
            if v.Kind=="Type":
                if v.Type=='enum':
                    typeContent+="typedef enum {"
                    for idx in range(len(v.Code)):
                        typeContent+=v.Code[idx].value
                        if idx!=len(v.Code)-1:
                            typeContent+=','
                    typeContent+="} "+v.Name+";"
                elif v.Type=='struct':
                    typeContent+="typedef struct {\n"
                    for elemK,elemV in v.FieldList.items():
                        typeContent+=gen_struct_elem(elemV)
                    typeContent+="}%s%s;\n"%(v.Name,sc.getArrSize(v.arrSize))
                else:
                    typeContent += "typedef %s %s%s;\n" % (sc.type_change(v.Type), v.changeName(),sc.getArrSize(v.arrSize))
        content+=typeContent
        print("====types_file")
        print(typeContent)
        writeFile=open("%s/include/kcg_types.h"%(sc.outputDir),'w')
        writeFile.write(content)
        
    def gen_assign_file(self):
        file=open('source_program/kcg_assign.txt','r')
        content=file.read()
        writeFile = open("%s/include/kcg_assign.h"%(sc.outputDir),'w')
        writeFile.write(content)

    # kcg_types.h需要依赖kcg_imported_types.h，目前的生成只需要简单拷贝
    def gen_imported_types_file(self):
        file=open('source_program/kcg_imported_types.txt','r')
        content=file.read()
        writeFile = open("%s/include/kcg_imported_types.h"%(sc.outputDir),'w')
        writeFile.write(content)

    # macro_libmathext64.h提供三角函数等基础函数的实现，目前的生成只需要简单拷贝
    def gen_macro_libmathext_file(self):
        file32 = open('source_program/macro_libmathext32.h', 'r')
        content32 = file32.read()
        writeFile32 = open("%s/include/macro_libmathext32.h"%(sc.outputDir), 'w')
        writeFile32.write(content32)

        file64 = open('source_program/macro_libmathext64.h', 'r')
        content64 = file64.read()
        writeFile64 = open("%s/include/macro_libmathext64.h"%(sc.outputDir), 'w')
        writeFile64.write(content64)

def testInputDirFiles():
    dir_path='./input'
    for root,dirs,files in os.walk(dir_path):
        for fileIdx in files:
            fileName=os.path.join(root,fileIdx)
            print("fileName=",fileName)
            sc.outputDir=os.path.splitext(os.path.basename(fileName))[0]
            dirPath=os.path.join("./output",sc.outputDir)
            sc.outputDir=dirPath
            print("====outputDir=",sc.outputDir)
            if not os.path.exists(dirPath):
                os.makedirs(dirPath)
                os.makedirs(os.path.join(dirPath,"include"))
                os.makedirs(os.path.join(dirPath,"src"))
            file=open(fileName,'r')
            strs=file.read()
            program,symboltable=sc.get_parse(strs)
            print("**************%s***********************",fileName)
            print(program)
            print("*************************************")
            gen=Scade_generate(program,symboltable)
            gen.gen_const_file()
            gen.gen_sensor_file()
            gen.gen_types_file()
            gen.gen_assign_file()
            gen.gen_imported_types_file()
            gen.gen_macro_libmathext_file()
            print("outputDir finish",sc.outputDir)

            global GlobalEnv
            GlobalEnv=None
            GlobalEnv=SymbolTable('Global')

def testInputFile(in_path:str,output_dir:str):
    sc.outputDir=os.path.splitext(os.path.basename(in_path))[0]
    dirPath=os.path.join(output_dir,sc.outputDir)
    sc.outputDir=dirPath
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
        os.makedirs(os.path.join(dirPath,"include"))
        os.makedirs(os.path.join(dirPath,"src"))
    file=open(in_path,'r')
    strs=file.read()
    program,symboltable=sc.get_parse(strs)
    print("*************************************",in_path)
    print(program)
    print("*************************************")
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()
    gen.gen_assign_file()
    gen.gen_imported_types_file()
    gen.gen_macro_libmathext_file()
    print("output_dir path: ",sc.outputDir)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--input_path',required=True,type=str)
    parser.add_argument('-o','--output_dir',required=True,type=str)
    args=parser.parse_args()
    #test files in input dir
    # testInputDirFiles()
    testInputFile(args.input_path,args.output_dir)
#     strs='''
# package P4
# function myAdd(in1:'T;in2:'T) returns(out1:'T) where 'T numeric
# let
# 	out1=in1+in2;
# tel
# end;

# package P5
# function func1(in1,in2:float64) returns(out1:float64)
# let
#     out1=P4::myAdd(in1,in2);
# tel
# end;
# '''
#     program,symboltable=sc.get_parse(strs)
#     print("*************************************")
#     print(program)
#     print("*************************************")
#     gen=Scade_generate(program,symboltable)
#     gen.gen_const_file()
#     gen.gen_sensor_file()
#     gen.gen_types_file()
#     gen.gen_assign_file()
#     gen.gen_imported_types_file()
#     gen.gen_macro_libmathext_file()




