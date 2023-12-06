#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "simple_automaton.h"
void simple_automaton(inC_simple_automaton *inC, outC_simple_automaton *outC)
{
SSM_ST state_sel = outC->state_nxt;
switch (state_sel)
{
case ADD1:
outC->o=inC->i+kcg_lit_int32(1);

if(inC->c & inC->d){
  outC->state_nxt = MINUS1;
}
break;

case MINUS1:
outC->o=inC->i-kcg_lit_int32(1);

if(inC->c | inC->d){
  outC->state_nxt = ADD1;
}
break;

}

}
void simple_automaton_init(outC_simple_automaton *outC)
{
outC->o=kcg_lit_int32(0);
outC->state_nxt=MINUS1;
}
void simple_automaton_reset(outC_simple_automaton *outC)
{
outC->state_nxt=MINUS1;
}
