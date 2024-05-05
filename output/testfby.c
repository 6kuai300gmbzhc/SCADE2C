#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testfby.h"
void testfby(inC_testfby *inC, outC_testfby *outC)
{
kcg_int8 fbyTmp;
outC->out1=inC->in1;
if(outC->init){
 for(int idx=0;idx<kcg_lit_int32(4);idx++){
outC->fbyArray[idx]=outC->out1;
}
outC->fbyIdx=0;
outC->init=kcg_false;
}
fbyTmp=outC->fbyArray[outC->fbyIdx];
outC->fbyArray[outC->fbyIdx]=inC->in1;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(4));
outC->out2=(fbyTmp+inC->in1);

}
void testfby_init(outC_testfby *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->out1=kcg_lit_int8(0);
outC->out2=kcg_lit_int8(0);
for(int idx=0;idx<kcg_lit_int32(4);idx++){
outC->fbyArray[idx]=kcg_lit_int8(0);
}
}
void testfby_reset(outC_testfby *outC)
{
}
