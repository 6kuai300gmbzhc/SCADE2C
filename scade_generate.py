import os
import copy
import scade_compile
from scade_compile import type_change,type_initial

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
                    content+="extern const "+type_change(v.Type)+" "+k+";"+"\n"
                else:
                    content+="#define "+k+" ("+type_initial(v.Type,v.Value)+")"
                    content+="\n"
        content+="\n\n#endif"
        print("const_file\n")
        print(content)
        with open('./output/kcg_const.h','w') as f:
            f.write(content)

    def gen_sensor_file(self):
        content="#ifndef _KCG_SENSORS_H_\n#define _KCG_SENSORS_H_\n#include \"kcg_types.h\"\n\n"
        for k, v in self.symboltable.SymbolTable.items():
            if v.Kind=="Sensor":
                content+="extern "+type_change(v.Type)+" "+k+";\n"
        content+="\n#endif"
        print("\n\nsensor_file")
        print(content)


if __name__=='__main__':
    print("main")
    strs = str("const e:bool=true;\
        d:int32=0;\
        imported c:int32;\
        private imported f:int8;\
        sensor tmp,tmp2:int32;\
        tmp3:bool;")
    # strs = str("function plus_two (x:int8) returns (y:int8) y=x+2;")
    program,symboltable=scade_compile.get_parse(strs)
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()
    gen.gen_sensor_file()




