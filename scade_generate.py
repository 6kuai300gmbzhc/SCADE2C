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
                if v.Type=='aray':
                    print(v.Code)
                    typeContent+="typedef %s %s%s;\n"%(type_change(v.Type),v.changeName(),getArrSize(v.Code))
                elif v.Type=='enum':
                    typeContent+="typedef enum {"
                    for idx in range(len(v.Code)):
                        typeContent+=v.Code[idx].value
                        if idx!=len(v.Code)-1:
                            typeContent+=','
                    typeContent+="} "+v.Name+";"
                else:
                    typeContent += "typedef %s %s;\n" % (type_change(v.Type), v.changeName())
        content+=typeContent
        print("====types_file")
        print(typeContent)
        writeFile=open('output/kcg_types.h','w')
        writeFile.write(content)


if __name__=='__main__':
    strs="type color2 = enum { Red, Blue, Yellow };\
    node activate2(in1,in2:int32;in3:color2) returns(out1,out2:int32)\
    let\
    activate when in3 match\
        | Red:\
        let\
        out1, out2 = (in1 - in2, 2)->pre(in1 + in2, 3);\
        tel\
        | Blue:\
        let\
        out1, out2 = fby(in2, in1;5;in1, in2);\
        tel\
        | Yellow:\
            let\
        out1, out2 = (5, 2);\
        tel\
    returns out1,out2;\
    tel"
    program,symboltable=scade_compile.get_parse(strs)
    print("*************************************")
    print(program)
    print("*************************************")
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()
    gen.gen_types_file()




