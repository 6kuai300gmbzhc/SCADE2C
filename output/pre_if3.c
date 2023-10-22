#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "pre_if3.h"
void pre_if3(inC_pre_if3 *inC, outC_pre_if3 *outC)
{
kcg_int8 initElem;
kcg_int8 ifTmp;
kcg_int8 initElem1;
if(outC->init){
initElem=kcg_lit_int8(1);
}else{
initElem=inC->input1;
}
if(inC->tmp){
ifTmp=(initElem);
}else{
ifTmp=inC->input2;
}
outC->output1 = ifTmp;
if(outC->init){
initElem1=outC->output1;
}else{
initElem1=(inC->input1+kcg_lit_int8(5));
}
outC->output2 = initElem1;
if(outC->init){outC->init=kcg_false;}
}
void pre_if3_init(outC_pre_if3 *outC)
{
outC->init=kcg_true;
outC->output1=kcg_lit_int8(0);
outC->output2=kcg_lit_int8(0);
}
void pre_if3_reset(outC_pre_if3 *outC)
{
}
