#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "strong_automaton.h"
void strong_automaton(inC_strong_automaton *inC, outC_strong_automaton *outC)
{
kcg_int32 initElem;
kcg_int32 initElem1;
SSM_ST state_act;
SSM_ST state_sel = outC->state_nxt;
switch (state_sel)
{
case ADD1:
if(inC->c & inC->d){
  state_act = MINUS1;
}
else {
state_act = state_sel;
}
break;

case MINUS1:
if(inC->c | inC->d){
  state_act = ADD1;
}
else {
state_act = state_sel;
}
break;

}
switch (state_act)
{
case ADD1:
if(outC->init){
initElem=kcg_lit_int32(100);
outC->init=kcg_false;
}else{
initElem=inC->i+kcg_lit_int32(1);
}
outC->o=initElem;

outC->state_nxt = state_act;
break;

case MINUS1:
if(outC->init1){
initElem1=kcg_lit_int32(2);
outC->init1=kcg_false;
}else{
initElem1=inC->i-kcg_lit_int32(1);
}
outC->o=initElem1;

outC->state_nxt = state_act;
break;

}

}
void strong_automaton_init(outC_strong_automaton *outC)
{
outC->init=kcg_true;
outC->init1=kcg_true;
outC->o=kcg_lit_int32(0);
outC->state_nxt=ADD1;
}
void strong_automaton_reset(outC_strong_automaton *outC)
{
outC->state_nxt=ADD1;
}
