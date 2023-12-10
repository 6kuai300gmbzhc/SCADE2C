#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "lnot_test.h"
void lnot_test(inC_lnot_test *inC, outC_lnot_test *outC)
{
kcg_uint8 initElem;
if(outC->init){
initElem=kcg_lit_uint8(0);
}else{
initElem=outC->mem_pre;
}
outC->output1 = initElem;
outC->mem_pre=inC->input1;
if(outC->init){outC->init=kcg_false;}
}
void lnot_test_init(outC_lnot_test *outC)
{
outC->mem_pre=kcg_lit_uint8(0);
outC->init=kcg_true;
outC->output1=kcg_lit_uint8(0);
outC->output2=kcg_lit_uint8(0);
}
void lnot_test_reset(outC_lnot_test *outC)
{
outC->mem_pre=kcg_lit_uint8(0);
}
