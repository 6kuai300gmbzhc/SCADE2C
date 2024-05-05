#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testControlBlockIf.h"
void testControlBlockIf(inC_testControlBlockIf *inC, outC_testControlBlockIf *outC)
{
kcg_int32 fbyTmp;
if(inC->in1<inC->in2)
{
if(inC->in2>inC->in5)
{
outC->out2 = kcg_lit_int32(1);
}
}
if(inC->in1<inC->in2)
{
if(inC->in2>inC->in5)
{
if(outC->init){
 for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=inC->in4;
}
outC->fbyIdx=0;
outC->init=kcg_false;
}
fbyTmp=outC->fbyArray[outC->fbyIdx];
outC->fbyArray[outC->fbyIdx]=inC->in3;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(5));
}
}
if(inC->in1<inC->in2)
{
if(inC->in2>inC->in5)
{
outC->out3 = fbyTmp;
}
}

}
void testControlBlockIf_init(outC_testControlBlockIf *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->out2=kcg_lit_int32(0);
outC->out3=kcg_lit_int32(0);
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=kcg_lit_int32(0);
}
}
void testControlBlockIf_reset(outC_testControlBlockIf *outC)
{
}
