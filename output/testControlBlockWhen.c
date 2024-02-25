#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testControlBlockWhen.h"
void testControlBlockWhen(inC_testControlBlockWhen *inC, outC_testControlBlockWhen *outC)
{
kcg_int32 fbyTmp;
kcg_int32 tmp_pre=outC->mem_pre;
kcg_int32 initTmp;
switch(inC->in5){
case FF :
{
if(outC->init1){
initTmp = inC->in3;
}else{
initTmp = tmp_pre;
}
break;
}
default :
break;
}
switch(inC->in5){
case FF :
{
outC->mem_pre = inC->in4;
break;
}
default :
break;
}
switch(inC->in5){
case TT :
{
outC->out2 = (inC->in3*inC->in4);
break;
}
case FF :
{
outC->out2 = initTmp;
break;
}
case XX :
{
switch(inC->in6){
case TT :
{
outC->out2 = inC->in3;
break;
}
case FF :
{
outC->out2 = inC->in4;
break;
}
case XX :
{
outC->out2 = inC->in7;
break;
}
default :
break;
}
break;
}
default :
break;
}
outC->out1 = (outC->out2*inC->in4);
switch(inC->in5){
case TT :
{
if(outC->init){
 for(int idx=0;idx<kcg_lit_int32(4);idx++){
outC->fbyArray[idx]=outC->out1;
}
outC->fbyIdx=0;
}
fbyTmp=outC->fbyArray[outC->fbyIdx];
outC->fbyArray[outC->fbyIdx]=inC->in3;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(4));
break;
}
default :
break;
}
switch(inC->in5){
case TT :
{
outC->out3 = fbyTmp;
break;
}
case FF :
{
outC->out3 = (inC->in4+inC->in3);
break;
}
case XX :
{
outC->out3 = inC->in3;
break;
}
default :
break;
}
if(outC->init){outC->init=kcg_false;}
if(outC->init1){outC->init1=kcg_false;}

}
void testControlBlockWhen_init(outC_testControlBlockWhen *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->mem_pre=kcg_lit_int32(0);
outC->init1=kcg_true;
outC->out1=kcg_lit_int32(0);
outC->out2=kcg_lit_int32(0);
outC->out3=kcg_lit_int32(0);
for(int idx=0;idx<kcg_lit_int32(4);idx++){
outC->fbyArray[idx]=kcg_lit_int32(0);
}
}
void testControlBlockWhen_reset(outC_testControlBlockWhen *outC)
{
outC->mem_pre=kcg_lit_int32(0);
}
