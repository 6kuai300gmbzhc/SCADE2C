import os
import copy
import scade_compile
from scade_compile import type_change,type_initial,objectsToString,getArrSize

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
        content="#ifndef _KCG_CONSTS_H_\n#define _KCG_CONSTS_H_\n#include \"kcg_types.h\"\n\n"
        for k,v in self.symboltable.SymbolTable.items():
            if v.Kind=="Const":
                if v.External==True:
                    content+="extern const %s %s%s;\n"%(type_change(v.Type),k,getArrSize(v.arrSize))
                else:#此处有问题，没有考虑数组的情况
                    content+="const %s %s%s=%s;\n"%(type_change(v.Type),k,getArrSize(v.arrSize),objectsToString(v.Code))
        content+="\n\n#endif"
        print("====const")
        print(content)
        with open('./output/kcg_const.h','w') as f:
            f.write(content)

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
        for k,v in self.symboltable.SymbolTable.items():
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


if __name__=='__main__':
    strs='''const imported c1:int32^2;
const c3:int32=4;
const imported c4:int32^2^(1+2);
sensor s1:float32^2;
type Tstr1={t1:int32};
const imported c5:unsigned<<8>>;
type t1=int32^2;
type t2={tt1:bool,tt2:int32,tt3:float32};
type t3={tt1:bool,tt2:int32,tt3:float32}^2;
type t4={tt1:bool,tt2:{tt3:int8,tt4:float32}};
type t5={tt1:bool,tt2:int32^2};
const imported c6:{tt1:bool,tt2:int32};
'''
    program,symboltable=scade_compile.get_parse(strs)
    print("*************************************")
    print(program)
    print("*************************************")
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()




