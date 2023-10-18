#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "fby_operator.h"
void fby_operator(inC_fby_operator *inC, outC_fby_operator *outC)
{
kcg_int8 ifTmp;
kcg_int8 initElem;
if(inC->tmp){
ifTmp=inC->input1;
}else{
ifTmp=inC->input2;
}
if(outC->init){
initElem=kcg_lit_int8(1);
}else{
initElem=(ifTmp);
}
outC->output1 = initElem;
if(outC->init){outC->init=kcg_false;}
}
void fby_operator_init(outC_fby_operator *outC)
{
outC->init=kcg_true;
outC->output1=kcg_lit_int8(0);
outC->output2=kcg_lit_int8(0);
}
void fby_operator_reset(outC_fby_operator *outC)
{
}
