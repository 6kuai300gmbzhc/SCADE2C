/* $******* SCADE Suite KCG 32-bit 6.6.1 beta (build i1) ********
** Command: kcg661.exe -config D:/坚果云同步目录/硕士毕业设计/SCADE相关资料/wss_scade_project/examples/examples/ABC_N/KCG/config.txt
** Generation date: 2023-10-07T17:41:44
*************************************************************$ */
#ifndef _simple_automaton_H_
#define _simple_automaton_H_

#include "kcg_types.h"

/* ========================  input structure  ====================== */
typedef struct {
  kcg_int32 /* i/ */ i;
  kcg_bool /* c/ */ c;
} inC_simple_automaton;

/* =====================  no output structure  ====================== */

/* ========================  context type  ========================= */
typedef struct {
  /* ---------------------------  outputs  --------------------------- */
  kcg_int32 /* o/ */ o;
  /* -----------------------  no local probes  ----------------------- */
  /* ----------------------- local memories  ------------------------- */
  SSM_ST /* _: */ state_nxt;
  /* -------------------- no sub nodes' contexts  -------------------- */
  /* ----------------- no clocks of observable data ------------------ */
} outC_simple_automaton;

/* ===========  node initialization and cycle functions  =========== */
/* simple_automaton/ */
extern void simple_automaton(
  inC_simple_automaton *inC,
  outC_simple_automaton *outC);

#ifndef KCG_NO_EXTERN_CALL_TO_RESET
extern void simple_automaton_reset(outC_simple_automaton *outC);
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */

#ifndef KCG_USER_DEFINED_INIT
extern void simple_automaton_init(outC_simple_automaton *outC);
#endif /* KCG_USER_DEFINED_INIT */



#endif /* _simple_automaton_H_ */
/* $******* SCADE Suite KCG 32-bit 6.6.1 beta (build i1) ********
** simple_automaton.h
** Generation date: 2023-10-07T17:41:44
*************************************************************$ */

