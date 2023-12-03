#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "activate1.h"
void activate1(inC_activate1 *inC, outC_activate1 *outC)
{
kcg_int32 initElem;
if(inC->in1!=kcg_lit_int32(0)){
if(outC->init){
initElem=inC->in1;
initElem=kcg_false;
}else{
initElem=outC->mem_pre;
}
outC->out1=initElem;
outC->mem_pre=inC->in1+inC->in2;
}else{
if(outC->init1)
{
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[outC->fbyIdx]=inC->in2;
}
outC->init1=kcg_false;
}
outC->out1=outC->fbyArray[outC->fbyIdx];
outC->fbyArray[outC->fbyIdx]=inC->in1;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(5));
}

}
void activate1_init(outC_activate1 *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->init=kcg_true;
outC->init1=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->out1=kcg_lit_int32(0);
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=kcg_lit_int32(0);
}
}
void activate1_reset(outC_activate1 *outC)
{
outC->mem_pre=kcg_lit_int32(0);
}
