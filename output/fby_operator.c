#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "fby_operator.h"
void fby_operator(inC_fby_operator *inC, outC_fby_operator *outC)
{
kcg_int8 tmp1;
kcg_int8 ifTmp;
kcg_int8 initElem;
kcg_int8 ifTmp1;
if(inC->tmp){
ifTmp=inC->input1;
}else{
ifTmp=inC->input2;
}
tmp1 = ifTmp;
if(outC->init)
{for(int idx=0;idx<kcg_lit_int32(4);idx++){
outC->fbyArray[outC->fbyIdx]=inC->input2+kcg_lit_int8(2);
}
}if(outC->init){
initElem=kcg_lit_int8(1);
}else{
initElem=outC->fbyArray[outC->fbyIdx];
}
outC->output2 = initElem;
outC->fbyArray[outC->fbyIdx]=inC->input1+kcg_lit_(2);
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(4));
if(inC->tmp){
ifTmp1=tmp1+kcg_lit_int8(1);
}else{
ifTmp1=tmp1+kcg_lit_int8(3);
}
outC->output1 = ifTmp1;
if(outC->init){outC->init=kcg_false;}
}
void fby_operator_init(outC_fby_operator *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->output1=kcg_lit_int8(0);
outC->output2=kcg_lit_int8(0);
for(int idx=0;idx<kcg_lit_int32(4);idx++){
outC->fbyArray[idx]=kcg_lit_int8(0);
}
}
void fby_operator_reset(outC_fby_operator *outC)
{
}
