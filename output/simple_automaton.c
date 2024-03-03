#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "simple_automaton.h"
void simple_automaton(inC_simple_automaton *inC, outC_simple_automaton *outC)
{
kcg_int32 initTmp;
kcg_int32 initTmp1;
SSM_ST state_sel = outC->state_nxt;
switch (state_sel)
{
case ADD1:
{

if((inC->c & inC->d)){
  outC->state_nxt = MINUS1;
}
break;
}

case MINUS1:
{

if((inC->c | inC->d)){
  outC->state_nxt = ADD1;
}
break;
}

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
