#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "example_1.h"
void example_1(inC_example_1 *inC, outC_example_1 *outC)
{
kcg_int32 _L1;
kcg_int32 initTmp;
kcg_int32 initTmp1;
SSM_ST state_sel = outC->state_nxt;
switch (state_sel)
{
case EVEN:
{
kcg_int32 _L2;
_L2=kcg_lit_int32(10);
if(outC->init){
initTmp=kcg_lit_int32(100);
outC->init=kcg_false;
}else{
initTmp=((inC->i+kcg_lit_int32(1))+_L2);
}
outC->o=initTmp;

if(inC->c){
  outC->state_nxt = ODD;
}
break;
}

case ODD:
{
if(outC->init1){
initTmp1=kcg_lit_int32(203);
outC->init1=kcg_false;
}else{
initTmp1=((-kcg_lit_int32(2))*inC->i);
}
outC->o=initTmp1;

if(inC->c){
  outC->state_nxt = EVEN;
}
break;
}

}

}
void example_1_init(outC_example_1 *outC)
{
outC->init=kcg_true;
outC->init1=kcg_true;
outC->o=kcg_lit_int32(0);
outC->state_nxt=EVEN;
}
void example_1_reset(outC_example_1 *outC)
{
outC->state_nxt=EVEN;
}
