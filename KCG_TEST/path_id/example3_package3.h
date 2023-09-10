/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-09T16:00:05
*************************************************************$ */
#ifndef _example3_package3_H_
#define _example3_package3_H_

#include "kcg_types.h"

/* ========================  input structure  ====================== */
typedef struct { kcg_int32 /* x/ */ x; } inC_example3_package3;

/* =====================  no output structure  ====================== */

/* ========================  context type  ========================= */
typedef struct {
  /* ---------------------------  outputs  --------------------------- */
  kcg_int32 /* y/ */ y;
  /* -----------------------  no local probes  ----------------------- */
  /* -----------------------  no local memory  ----------------------- */
  /* -------------------- no sub nodes' contexts  -------------------- */
  /* ----------------- no clocks of observable data ------------------ */
} outC_example3_package3;

/* ===========  node initialization and cycle functions  =========== */
/* package3::example3/ */
extern void example3_package3(
  inC_example3_package3 *inC,
  outC_example3_package3 *outC);

#ifndef KCG_NO_EXTERN_CALL_TO_RESET
extern void example3_reset_package3(outC_example3_package3 *outC);
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */

#ifndef KCG_USER_DEFINED_INIT
extern void example3_init_package3(outC_example3_package3 *outC);
#endif /* KCG_USER_DEFINED_INIT */



#endif /* _example3_package3_H_ */
/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** example3_package3.h
** Generation date: 2023-09-09T16:00:05
*************************************************************$ */

