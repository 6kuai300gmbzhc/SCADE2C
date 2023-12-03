#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "test_last.h"
void test_last(inC_test_last *inC, outC_test_last *outC)
{
kcg_int8 tvar1;
if(outC->init)
{
for(int idx=0;idx<kcg_lit_int32(1)+kcg_lit_int32(2);idx++){
outC->fbyArray[outC->fbyIdx]=inC->in1-kcg_lit_int8(1);
}
}
if(outC->init)
{
for(int idx=0;idx<kcg_lit_int32(1)+kcg_lit_int32(2);idx++){
outC->fbyArray1[outC->fbyIdx1]=inC->in2+kcg_lit_int8(3);
}
}
tvar1=inC->in1+inC->in2;
outC->out1=outC->fbyArray[outC->fbyIdx];
outC->out2=outC->fbyArray1[outC->fbyIdx1];
outC->fbyArray[outC->fbyIdx]=inC->in1+kcg_lit_int8(1);
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(1)+kcg_lit_int32(2));
outC->fbyArray1[outC->fbyIdx1]=inC->in1+kcg_lit_int8(2);
outC->fbyIdx1=(outC->fbyIdx1+1)%(kcg_lit_int32(1)+kcg_lit_int32(2));
if(outC->init){outC->init=kcg_false;}
}
void test_last_init(outC_test_last *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->fbyIdx1=kcg_lit_int32(0);
outC->out1=kcg_lit_int8(0);
outC->out2=kcg_lit_int8(0);
for(int idx=0;idx<kcg_lit_int32(1)+kcg_lit_int32(2);idx++){
outC->fbyArray[idx]=kcg_lit_int8(0);
}
for(int idx=0;idx<kcg_lit_int32(1)+kcg_lit_int32(2);idx++){
outC->fbyArray1[idx]=kcg_lit_int8(0);
}
}
void test_last_reset(outC_test_last *outC)
{
}
