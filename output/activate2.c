#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "activate2.h"
void activate2(inC_activate2 *inC, outC_activate2 *outC)
{
kcg_int32 initElem;
kcg_int32 initElem1;
switch(inC->in3){
case Red :
if(outC->init){
initElem=inC->in1-inC->in2;
outC->init=kcg_false;
}else{
initElem=outC->mem_pre;
}
if(outC->init1){
initElem1=kcg_lit_int32(2);
outC->init1=kcg_false;
}else{
initElem1=outC->mem_pre1;
}
outC->out1=initElem;
outC->out2=initElem1;
outC->mem_pre=inC->in1+inC->in2;
outC->mem_pre1=kcg_lit_int32(3);
break;
case Blue :
if(outC->init2)
{
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[outC->fbyIdx]=inC->in1;
}
outC->init2=kcg_false;
outC->fbyIdx=0;
}
if(outC->init3)
{
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray1[outC->fbyIdx1]=inC->in2;
}
outC->init3=kcg_false;
outC->fbyIdx1=0;
}
outC->out1=outC->fbyArray[outC->fbyIdx];
outC->out2=outC->fbyArray1[outC->fbyIdx1];
outC->fbyArray[outC->fbyIdx]=inC->in2;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(5));
outC->fbyArray1[outC->fbyIdx1]=inC->in1;
outC->fbyIdx1=(outC->fbyIdx1+1)%(kcg_lit_int32(5));
break;
case Yellow :
outC->out1=kcg_lit_int32(5);
outC->out2=kcg_lit_int32(2);
break;
default : 
 break;
}
}
void activate2_init(outC_activate2 *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->mem_pre1=kcg_lit_int32(0);
outC->init=kcg_true;
outC->init1=kcg_true;
outC->init2=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->init3=kcg_true;
outC->fbyIdx1=kcg_lit_int32(0);
outC->out1=kcg_lit_int32(0);
outC->out2=kcg_lit_int32(0);
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=kcg_lit_int32(0);
}
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray1[idx]=kcg_lit_int32(0);
}
}
void activate2_reset(outC_activate2 *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->mem_pre1=kcg_lit_int32(0);
}
