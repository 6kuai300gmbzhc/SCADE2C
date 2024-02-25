#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testControlBlockIf2.h"
void testControlBlockIf2(inC_testControlBlockIf2 *inC, outC_testControlBlockIf2 *outC)
{
kcg_int32 tmp_pre=outC->mem_pre;
kcg_int32 initTmp;
kcg_int32 tmp_pre1=outC->mem_pre1;
kcg_int32 initTmp1;
kcg_int32 fbyTmp;
kcg_int32 tmp_pre2=outC->mem_pre2;
kcg_int32 initTmp2;
if((inC->in1<inC->in2)){
if(outC->init){
initTmp = kcg_lit_int32(1);
}else{
initTmp = tmp_pre;
}
}
if((inC->in1<inC->in2)){
outC->mem_pre = inC->in3;
}
if(!(inC->in1<inC->in2)){
if((inC->in2>inC->in5)){
if(outC->init1){
initTmp1 = inC->in3;
}else{
initTmp1 = tmp_pre1;
}
}
}
if(!(inC->in1<inC->in2)){
if((inC->in2>inC->in5)){
outC->mem_pre1 = inC->in4;
}
}
if(!(inC->in1<inC->in2)){
if((inC->in2>inC->in5)){
if(outC->init2){
 for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=inC->in4;
}
outC->fbyIdx=0;
}
fbyTmp=outC->fbyArray[outC->fbyIdx];
outC->fbyArray[outC->fbyIdx]=inC->in3;
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(5));
}
}
if(!(inC->in1<inC->in2)){
if(!(inC->in2>inC->in5)){
if(outC->init3){
initTmp2 = kcg_lit_int32(1);
}else{
initTmp2 = tmp_pre2;
}
}
}
if(!(inC->in1<inC->in2)){
if(!(inC->in2>inC->in5)){
outC->mem_pre2 = inC->in4;
}
}
if((inC->in1<inC->in2)){
outC->out2 = initTmp;
}else{
if((inC->in2>inC->in5)){
outC->out2 = initTmp1;
}else{
outC->out2 = initTmp2;
}
}
if((inC->in1<inC->in2)){
switch(inC->in6){
case TT :
{
outC->out3 = inC->in3;
break;
}
case FF :
{
outC->out3 = inC->in4;
break;
}
case XX :
{
outC->out3 = (inC->in3+inC->in4);
break;
}
default :
break;
}
}else{
if((inC->in2>inC->in5)){
outC->out3 = fbyTmp;
}else{
outC->out3 = inC->in4;
}
}
if(outC->init){outC->init=kcg_false;}
if(outC->init1){outC->init1=kcg_false;}
if(outC->init2){outC->init2=kcg_false;}
if(outC->init3){outC->init3=kcg_false;}

}
void testControlBlockIf2_init(outC_testControlBlockIf2 *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->init=kcg_true;
outC->mem_pre1=kcg_lit_int32(0);
outC->init1=kcg_true;
outC->init2=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->mem_pre2=kcg_lit_int32(0);
outC->init3=kcg_true;
outC->out2=kcg_lit_int32(0);
outC->out3=kcg_lit_int32(0);
for(int idx=0;idx<kcg_lit_int32(5);idx++){
outC->fbyArray[idx]=kcg_lit_int32(0);
}
}
void testControlBlockIf2_reset(outC_testControlBlockIf2 *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->mem_pre1=kcg_lit_int32(0);
outC->mem_pre2=kcg_lit_int32(0);
}
