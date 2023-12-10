
#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "simple_automaton.h"

/* simple_automaton/ */
void simple_automaton(inC_simple_automaton *inC, outC_simple_automaton *outC)
{
  /* _: */
  SSM_ST state_sel;

  state_sel = outC->state_nxt;
  /* _: */
  switch (state_sel) {
    case SSM_st_MINUS1 :
      outC->o = inC->i - kcg_lit_int32(1);
      if (inC->c) {
        outC->state_nxt = SSM_st_ADD1;
      }
      else {
        outC->state_nxt = SSM_st_MINUS1;
      }
      break;
    case SSM_st_ADD1 :
      outC->o = inC->i + kcg_lit_int32(1);
      if (inC->c) {
        outC->state_nxt = SSM_st_MINUS1;
      }
      else {
        outC->state_nxt = SSM_st_ADD1;
      }
      break;
    default :
      /* this default branch is unreachable */
      break;
  }
}

#ifndef KCG_USER_DEFINED_INIT
void simple_automaton_init(outC_simple_automaton *outC)
{
  outC->o = kcg_lit_int32(0);
  outC->state_nxt = SSM_st_ADD1;
}
#endif /* KCG_USER_DEFINED_INIT */


#ifndef KCG_NO_EXTERN_CALL_TO_RESET
void simple_automaton_reset(outC_simple_automaton *outC)
{
  outC->state_nxt = SSM_st_ADD1;
}
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */



/* $******* SCADE Suite KCG 32-bit 6.6.1 beta (build i1) ********
** simple_automaton.c
** Generation date: 2023-10-07T17:41:44
*************************************************************$ */

