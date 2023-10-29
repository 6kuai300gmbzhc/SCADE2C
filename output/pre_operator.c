#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "pre_operator.h"
void pre_operator(inC_pre_operator *inC, outC_pre_operator *outC)
{
kcg_float64 initElem;
if(outC->init){
initElem=inC->input1;
}else{
initElem=inC->input2;
}
outC->output1=initElem;
outC->output2=inC->input1+inC->input2;
if(outC->init){outC->init=kcg_false;}
}
void pre_operator_init(outC_pre_operator *outC)
{
outC->init=kcg_true;
outC->output1=kcg_lit_float64(0.0);
outC->output2=kcg_lit_float64(0.0);
}
void pre_operator_reset(outC_pre_operator *outC)
{
}
