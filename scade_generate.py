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


if __name__=='__main__':
    # file=open('source_program/PFD.txt','r')
    # strs=file.read()
#     strs='''node vwtovr(vw : float64 last = 70)
#   returns (vr : float64 default = 70 last = 70)
# var
#   _L1 : float64;
#   _L2 : float64;
#   _L3 : float64;
#   _L4 : float64;
#   _L5 : float64;
#   _L6 : float64;
#   _L8 : bool;
# let
#   _L1= (70)  -> (_L2);
#   _L2=  pre (_L5);
#   _L3= _L1  - _L4;
#   _L4= 0.09;
#   _L5=  if _L8 then (_L6) else (_L3);
#   _L6= vw;
#   _L8= _L3  < _L6;
#   vr= _L5;
# tel'''
    strs='''node strong_automaton (i: int32; c: bool; d: bool) returns (o: int32)
    automaton
        initial state ADD1
        unless if c and d restart MINUS1;
        let
            o = 100 -> i + 1 ;
        tel
    
        state MINUS1
        unless if c or d restart ADD1;
        let
            o = 2 -> i - 1 ;
        tel
    returns o;'''
    program,symboltable=scade_compile.get_parse(strs)
    print("*************************************")
    print(program)
    print("*************************************")
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()




