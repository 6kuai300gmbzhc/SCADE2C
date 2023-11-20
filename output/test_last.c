#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "test_last.h"
void test_last(inC_test_last *inC, outC_test_last *outC)
{
kcg_int8 tvar1;
kcg_int8 initElem;
if(outC->init){
initElem=inC->in1-inC->in2;
}else{
initElem=outC->mem_pre;
}
tvar1=inC->in1+inC->in2;
outC->out1=initElem;
outC->out2=tvar1+outC->out1;
outC->mem_pre=outC->out2+tvar1;
if(outC->init){outC->init=kcg_false;}
}
void test_last_init(outC_test_last *outC)
{
outC->mem_pre=kcg_lit_int8(0);
outC->init=kcg_true;
outC->out1=kcg_lit_int8(0);
outC->out2=kcg_lit_int8(0);
}
void test_last_reset(outC_test_last *outC)
{
outC->mem_pre=kcg_lit_int8(0);
}
