import os
import copy
import scade_compile
from scade_compile import type_change

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
                    content+="#define "+k+" "
                    if v.Type=="bool":
                        content+="kcg_"+v.Value
                    else:
                        content+="(kcg_lit_"+v.Type+"("+str(v.Value)+"))"
                    content+="\n"
        content+="\n\n#endif"
        print(content)
        with open('./output/kcg_const.h','w') as f:
            f.write(content)

if __name__=='__main__':
    print("main")
    strs = str("package NoPackage\
        const e:bool=true;\
        const d:int32=0;\
        const imported c:int32;\
        const private imported f:int8;\
        end;")
    program,symboltable=scade_compile.get_parse(strs)
    gen=Scade_generate(program,symboltable)
    gen.gen_const_file()




