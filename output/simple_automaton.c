#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "simple_automaton.h"
void simple_automaton(inC_simple_automaton *inC, outC_simple_automaton *outC)
{
kcg_int32 initElem;
kcg_int32 initElem1;
SSM_ST state_sel = outC->state_nxt;
switch (state_sel)
{
case ADD1:
if(outC->init){
initElem=kcg_lit_int32(100);
outC->init=kcg_false;
}else{
initElem=inC->i+kcg_lit_int32(1);
}
outC->o=initElem;

if(inC->c & inC->d){
  outC->state_nxt = MINUS1;
}
break;

case MINUS1:
if(outC->init1){
initElem1=kcg_lit_int32(2);
outC->init1=kcg_false;
}else{
initElem1=inC->i-kcg_lit_int32(1);
}
outC->o=initElem1;

if(inC->c | inC->d){
  outC->state_nxt = ADD1;
}
break;

}

}
void simple_automaton_init(outC_simple_automaton *outC)
{
outC->init=kcg_true;
outC->init1=kcg_true;
outC->o=kcg_lit_int32(0);
outC->state_nxt=MINUS1;
}
void simple_automaton_reset(outC_simple_automaton *outC)
{
outC->state_nxt=MINUS1;
}
