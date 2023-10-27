import os
import copy
import scade_compile
from scade_compile import type_change,type_initial,objectsToString,getArrSize

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
                else:
                    content+="const %s %s=%s;\n"%(type_change(v.Type),k,objectsToString(v.Code))
        content+="\n\n#endif"
        print("====const")
        print(content)
        with open('./output/kcg_const.h','w') as f:
            f.write(content)

    def gen_sensor_file(self):
        content="#ifndef _KCG_SENSORS_H_\n#define _KCG_SENSORS_H_\n#include \"kcg_types.h\"\n\n"
        for k, v in self.symboltable.SymbolTable.items():
            if v.Kind=="Sensor":
                content+="extern %s %s%s;\n"%(type_change(v.Type),k,getArrSize(v.Code))
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
                if len(v.Code)==0: #不是数组
                    typeContent+="typedef %s %s;\n"%(type_change(v.Type),v.changeName())
                else:
                    typeContent+="typedef %s %s%s;\n"%(type_change(v.Type),v.changeName(),getArrSize(v.Code))
        content+=typeContent
        print("====types_file")
        print(typeContent)
        writeFile=open('output/kcg_types.h','w')
        writeFile.write(content)


if __name__=='__main__':
    print("main")
    # strs = str("const e:bool=true;\
    #     d:int32=0;\
    #     imported c:int32^2;\
    #     private imported f:int8;\
    #     sensor tmp,tmp2:int32;\
    #     tmp3:bool;")
    # strs = str("node init_operator(input1:int8) returns(output1:int8) output1=0->input1;")
#     strs=str("node pre_example(input1,input2:int32) returns (output1,output2 : int32)\
# let\
#     output2=input1+input2;\
# 	output1=1-> (pre input1);\
# tel")tet
#     strs=str("node fby_operator(input1,input2:int8;tmp:bool) returns(output1,output2:int8)\
# let \
# output1= 1->(if tmp then input1 else input2);\
# tel")
    strs=str("type type1=float32^2;\
type2=int32;\
typ3=int8^(1+1)^3;\
type6=int8^2^3^4;\
const e : bool = true;\
const d: int32 = 0;\
const imported c: int32^2;\
const private imported f: int8;\
    sensor sensor1:float32;\
    sensor2: float32 ^ 2;\
node fby_operator(input1,input2:int8) returns(output1,output2:int8)\
var \
tmp:int8;\
let \
tmp=input1+2;\
output2=tmp+2;\
output2=1->last 'tmp;\
tel\
")
    program,symboltable=scade_compile.get_parse(strs)
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()




