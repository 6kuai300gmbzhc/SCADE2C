import os
import copy
import scade_compile
from scade_compile import getArrSize,type_change,getRootSymbolTable,objectsToString

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
                    content+="const %s %s%s=%s;\n"%(type_change(v.Type),k,getArrSize(v.arrSize),objectsToString(v.Code,self.symboltable))
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
        
if __name__=='__main__':
    #test files in input dir
    # testInputDirFiles()
#     strs='''node arrayTextTest1(in1,in2,in3:int8) returns(o1:int8^3;o3:int8)
# let
# 	o1=[in1,in2,in3];
# 	o3=o1[1];
# tel'''
#     strs='''node arrayTextTest5(in1:int8^2^3^4) returns(o1:int8^2^3^4)
# let
# 	o1=in1;
# tel'''
#     strs='''type struct6={tt1:int8^2};
# node arrayTextTest10(in1,in2:int8) returns(o1:struct6)
# let
# 	o1={tt1:[in1,in2]};
# tel'''
    strs='''
        function Square(Square_In : float64) returns (Square_Out : float64)
        var
        _L1 : float64;
        _L2 : float64;
        let
            _L1= Square_In;
            _L2= _L1 * _L1;
            Square_Out= _L2;
        tel

        function testCosR(x : float64) returns (y : float64)
        let 
            y = Square(x);
        tel
'''
#     strs='''type struct5={tt1:int8,tt2:bool};
# node arrayTextTest9(in1:int8;in3:bool;in2:struct5) returns(o1:struct5^2)
# let
# 	o1=[{tt1:in1,tt2:in3},in2];
# tel'''
#     strs='''type struct5={tt1:int8,tt2:bool};
# node arrayTextTest9(in1,in2:int8;in3,in4:bool;in5,in6:struct5;in7:struct5^2) returns(o1:struct5^2^3;o2:int8)
# let
# 	o1=[[{tt1:o2,tt2:in3},in5],in7,[in6,{tt1:in2,tt2:in4}]];
# 	o2=in1+in2;
# tel'''
    program,symboltable=scade_compile.get_parse(strs)
    print("*************************************")
    print(program)
    print("*************************************")
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()
    gen.gen_macro_libmathext64_file()



