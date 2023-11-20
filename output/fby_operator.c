#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "fby_operator.h"
void fby_operator(inC_fby_operator *inC, outC_fby_operator *outC)
{
kcg_int8 initElem;
kcg_int8 initElem1;
if(outC->init){
initElem=kcg_lit_int8(1);
}else{
initElem=outC->mem_pre;
}
if(outC->init){
initElem1=kcg_lit_int8(2);
}else{
initElem1=outC->mem_pre1;
}
outC->output1=initElem;
outC->output2=initElem1;
outC->mem_pre=inC->input1;
outC->mem_pre1=inC->input2;
if(outC->init){outC->init=kcg_false;}
}
void fby_operator_init(outC_fby_operator *outC)
{
outC->mem_pre=kcg_lit_int8(0);
outC->mem_pre1=kcg_lit_int8(0);
outC->init=kcg_true;
outC->output1=kcg_lit_int8(0);
outC->output2=kcg_lit_int8(0);
}
void fby_operator_reset(outC_fby_operator *outC)
{
outC->mem_pre=kcg_lit_int8(0);
outC->mem_pre1=kcg_lit_int8(0);
}
