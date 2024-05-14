import os
import copy
import scade_compile
from scade_compile import getArrSize,type_change,getRootSymbolTable,objectsToString
from queue import Queue

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
        temp = self.symboltable
        que = Queue()
        que.put(temp)
        while not que.empty(): # 广搜，处理存在包的情况下，符号表层层嵌套的情况
            temp = que.get()
            for k,v in temp.SymbolTable.items():
                if v.Kind=="Const":
                    if v.External==True:
                        content+="extern const %s %s%s;\n"%(type_change(v.Type),k + v.PackageName,getArrSize(v.arrSize))
                    else:#此处有问题，没有考虑数组的情况
                        content+="const %s %s%s = %s;\n"%(type_change(v.Type),k + v.PackageName,getArrSize(v.arrSize),objectsToString(v.Code,temp,temp.EnvName))
            for table in temp.ChildTableList:
                que.put(table)
        # for k,v in self.symboltable.SymbolTable.items():
        #     if v.Kind=="Const":
        #         if v.External==True:
        #             content+="extern const %s %s%s;\n"%(type_change(v.Type),k,getArrSize(v.arrSize))
        #         else:#此处有问题，没有考虑数组的情况
        #             content+="const %s %s%s=%s;\n"%(type_change(v.Type),k,getArrSize(v.arrSize),objectsToString(v.Code,self.symboltable,self.symboltable.EnvName))
        content+="\n\n#endif"
        print("====const")
        print(content)
        with open('./output/kcg_consts.h','w') as f:
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
        symbolTable=getRootSymbolTable(self.symboltable)
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
    def gen_macro_libmathext64_file(self):
        file = open('source_program/macro_libmathext64.h', 'r')
        content = file.read()
        writeFile = open('output/macro_libmathext64.h', 'w')
        writeFile.write(content)

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
            gen.gen_macro_libmathext64_file()
            # kcg_types.h需要依赖kcg_assign.h, 目前的生成只需要简单的拷贝


if __name__=='__main__':
    #test files in input dir
    # testInputDirFiles()
    strs='''
node vwtovr(vw : float64 last = 70)
  returns (vr : float64 default = 70 last = 70)
var
  _L1 : float64;
  _L2 : float64;
  _L3 : float64;
  _L4 : float64;
  _L5 : float64;
  _L6 : float64;
  _L8 : bool;
let
  _L1= (70) #1 -> (_L2);
  _L2= #1 pre (_L5);
  _L3= _L1 #1 - _L4;
  _L4= 0.09;
  _L5= #1 if _L8 then (_L6) else (_L3);
  _L6= vw;
  _L8= _L3 #1 < _L6;
  vr= _L5;
tel

node err(vw : float64) returns (err : float64 last = 0.0)
var
  _L1 : float64;
  _L2 : float64;
  _L3 : float64;
  _L4 : float64;
  _L5 : float64;
  _L6 : bool;
  _L7 : float64;
let
  err= _L4;
  _L1= vw;
  _L2= #1 vwtovr(_L1);
  _L3= _L2 #1 - _L1;
  _L4= #1 if _L6 then (_L3) else (_L7);
  _L5= 0;
  _L6= _L3 #1 > _L5;
  _L7= 0;
tel'''
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
    gen.gen_macro_libmathext64_file()




