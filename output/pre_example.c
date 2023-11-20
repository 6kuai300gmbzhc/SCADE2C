#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "pre_example.h"
void pre_example(inC_pre_example *inC, outC_pre_example *outC)
{
kcg_int32 initElem;
outC->output2 = inC->input1+inC->input2;
if(outC->init){
initElem=kcg_lit_int32(1);
}else{
initElem=(outC->mem_pre);
}
outC->output1 = initElem;
outC->mem_pre=inC->input1;
if(outC->init){outC->init=kcg_false;}
}
void pre_example_init(outC_pre_example *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->init=kcg_true;
outC->output1=kcg_lit_int32(0);
outC->output2=kcg_lit_int32(0);
}
void pre_example_reset(outC_pre_example *outC)
{
outC->mem_pre=kcg_lit_int32(0);
}
