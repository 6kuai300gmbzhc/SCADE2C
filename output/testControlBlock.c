#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testControlBlock.h"
void testControlBlock(inC_testControlBlock *inC, outC_testControlBlock *outC)
{
kcg_int8 initTmp;
kcg_int8 initTmp1;
kcg_int8 tmp_pre=outC->mem_pre;
kcg_int8 initTmp2;
if((inC->in1>inC->in2)){
if((inC->in1>inC->in3)){
if(outC->init){
initTmp = kcg_lit_int8(1);
}else{
initTmp = inC->in1;
}
}
}
if(!(inC->in1>inC->in2)){
if(outC->init1){
initTmp1 = kcg_lit_int8(2);
}else{
initTmp1 = inC->in2;
}
}
outC->mem_pre = inC->in3;
if((inC->in1>inC->in2)){
if((inC->in1>inC->in3)){
outC->out3 = initTmp;
}else{
outC->out3 = inC->in1;
}
}else{
outC->out3 = initTmp1;
}
if(outC->init2){
initTmp2 = outC->out3;
}else{
initTmp2 = tmp_pre;
}
outC->out1 = initTmp2;
if((inC->in1>inC->in2)){
if((inC->in1>inC->in3)){
outC->out2 = outC->out1;
}else{
outC->out2 = outC->out3;
}
}else{
outC->out2 = outC->out1;
}
if(outC->init){outC->init=kcg_false;}
if(outC->init1){outC->init1=kcg_false;}
if(outC->init2){outC->init2=kcg_false;}

}
void testControlBlock_init(outC_testControlBlock *outC)
{
outC->init=kcg_true;
outC->init1=kcg_true;
outC->mem_pre=kcg_lit_int8(0);
outC->init2=kcg_true;
outC->out1=kcg_lit_int8(0);
outC->out2=kcg_lit_int8(0);
outC->out3=kcg_lit_int8(0);
}
void testControlBlock_reset(outC_testControlBlock *outC)
{
outC->mem_pre=kcg_lit_int8(0);
}
