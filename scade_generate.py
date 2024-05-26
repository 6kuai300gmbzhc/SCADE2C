import os
import copy
import scade_compile
from scade_compile import getArrSize,type_change,objectsToString
from queue import Queue
from scade_compile_otherFunc import GlobalEnv

def gen_struct_elem(elem):
    str=""
    if elem.Type=='struct':
        str+="struct {\n"
        for elemK,elemV in elem.FieldList.items():
            str+=gen_struct_elem(elemV)
        str+="}%s%s;\n"%(elem.Name,getArrSize(elem.arrSize))
    else:
        str+="%s %s%s;\n"%(type_change(elem.Type),elem.Name,getArrSize(elem.arrSize))
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
                    h_content += "extern const %s %s%s;\n"%(type_change(v.Type),k+v.PackageName,getArrSize(v.arrSize))
                    if v.External !=True:
                        c_content += "const %s %s%s = %s;\n"%(type_change(v.Type),k + v.PackageName,getArrSize(v.arrSize),objectsToString(v.Code,temp,temp.EnvName))
            for table in temp.ChildTableList:
                que.put(table)
        h_content+="\n\n#endif"
        print("====const h_file")
        print(h_content)
        print("====const c_file")
        print(c_content)
        with open('./output/kcg_consts.h','w') as f:
            f.write(h_content)
        with open('./output/kcg_consts.c','w') as f:
            f.write(c_content)    

    def gen_sensor_file(self):
        content="#ifndef _KCG_SENSORS_H_\n#define _KCG_SENSORS_H_\n#include \"kcg_types.h\"\n\n"
        for k, v in self.symboltable.SymbolTable.items():
            if v.Kind=="Sensor":
                content+="extern %s %s%s;\n"%(type_change(v.Type),k,getArrSize(v.arrSize))
        content+="\n#endif"
        print("====sensor")
        print(content)
        with open('./output/kcg_sensors.h','w') as f:
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
                    typeContent+="}%s%s;\n"%(v.Name,getArrSize(v.arrSize))
                else:
                    typeContent += "typedef %s %s%s;\n" % (type_change(v.Type), v.changeName(),getArrSize(v.arrSize))
        content+=typeContent
        print("====types_file")
        print(typeContent)
        writeFile=open('output/kcg_types.h','w')
        writeFile.write(content)
        
    def gen_assign_file(self):
        file=open('source_program/kcg_assign.txt','r')
        content=file.read()
        writeFile = open('output/kcg_assign.h','w')
        writeFile.write(content)

    # kcg_types.h需要依赖kcg_imported_types.h，目前的生成只需要简单拷贝
    def gen_imported_types_file(self):
        file=open('source_program/kcg_imported_types.txt','r')
        content=file.read()
        writeFile = open('output/kcg_imported_types.h','w')
        writeFile.write(content)

    # macro_libmathext64.h提供三角函数等基础函数的实现，目前的生成只需要简单拷贝
    def gen_macro_libmathext_file(self):
        file32 = open('source_program/macro_libmathext32.h', 'r')
        content32 = file32.read()
        writeFile32 = open('output/macro_libmathext32.h', 'w')
        writeFile32.write(content32)

        file64 = open('source_program/macro_libmathext64.h', 'r')
        content64 = file64.read()
        writeFile64 = open('output/macro_libmathext64.h', 'w')
        writeFile64.write(content64)

def testInputDirFiles():
    dir_path='./input'
    for root,dirs,files in os.walk(dir_path):
        for fileIdx in files:
            fileName=os.path.join(root,fileIdx)
            file=open(fileName,'r')
            strs=file.read()
            program,symboltable=scade_compile.get_parse(strs)
            print("**************%s***********************",fileName)
            print(program)
            print("*************************************")
            gen=Scade_generate(program,symboltable)
            gen.gen_const_file()
            gen.gen_sensor_file()
            gen.gen_types_file()
            gen.gen_macro_libmathext_file()
            # kcg_types.h需要依赖kcg_assign.h, 目前的生成只需要简单的拷贝


if __name__=='__main__':
    #test files in input dir
    # testInputDirFiles()
#     strs='''package P4
# function myAdd(in1:int64;in2:int64) returns(out1:int64)
# let
# 	out1=in1+in2;
# tel
# end;'''
    strs='''
package P4
function myAdd(in1:'T;in2:'T) returns(out1:'T) where 'T numeric
let
	out1=in1+in2;
tel
end;

package P5
function func1(in1,in2:float64) returns(out1:float64)
let
    out1=P4::myAdd(in1,in2);
tel
end;'''
#     strs='''
# package P1
# function func1(in1:int64) returns(out1:int64)
# let
# 	out1=in1+2;
# tel
# package pp1
# function func2(in1:int64) returns(out1:int64)
# let
# 	out1=in1-2;
# tel
# end;
# end;

# package P2
# package P3
# function func3(in1:int64) returns(out1:int64)
# let
# 	out1=in1+1;
# tel
# end;
# function func2(in1:int64) returns(out1,out2,out3:int64)
# let
# 	out1=P1::func1(in1);
# 	out2=P1::pp1::func2(in1);
# 	out3=P3::func3(in1);
# tel
# end;'''
    program,symboltable=scade_compile.get_parse(strs)
    print("*************************************")
    print(program)
    print("*************************************")
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()
    gen.gen_assign_file()
    gen.gen_imported_types_file()
    gen.gen_macro_libmathext_file()




