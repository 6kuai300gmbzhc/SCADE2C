/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-10T21:54:08
*************************************************************$ */
#ifndef _N_H_
#define _N_H_

#include "kcg_types.h"
#include "f_10.h"

/* ========================  input structure  ====================== */
typedef struct { array_int32_10 /* a1/ */ a1; } inC_N;

/* =====================  no output structure  ====================== */

/* ========================  context type  ========================= */
typedef struct {
  /* ---------------------------  outputs  --------------------------- */
  kcg_int32 /* o1/ */ o1;
  /* -----------------------  no local probes  ----------------------- */
  /* -----------------------  no local memory  ----------------------- */
  /* -------------------- no sub nodes' contexts  -------------------- */
  /* ----------------- no clocks of observable data ------------------ */
} outC_N;

/* ===========  node initialization and cycle functions  =========== */
/* N/ */
extern void N(inC_N *inC, outC_N *outC);

#ifndef KCG_NO_EXTERN_CALL_TO_RESET
extern void N_reset(outC_N *outC);
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */

#ifndef KCG_USER_DEFINED_INIT
extern void N_init(outC_N *outC);
#endif /* KCG_USER_DEFINED_INIT */



#endif /* _N_H_ */
/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** N.h
** Generation date: 2023-09-10T21:54:08
*************************************************************$ */

