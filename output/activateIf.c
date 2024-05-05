#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "activateIf.h"
void activateIf(inC_activateIf *inC, outC_activateIf *outC)
{
if(inC->in1>kcg_lit_int32(0)){
if(outC->init)
{
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=inC->in2;
}
outC->init=kcg_false;
outC->fbyIdx=0;
}
outC->out=outC->fbyArray[outC->fbyIdx];
outC->fbyArray[outC->fbyIdx]=inC->in1;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(5));
}else{
outC->out=inC->in1;
}

}
void activateIf_init(outC_activateIf *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->out=kcg_lit_int32(0);
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=kcg_lit_int32(0);
}
}
void activateIf_reset(outC_activateIf *outC)
{
}
