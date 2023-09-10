/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-09T15:48:40
*************************************************************$ */
#ifndef _example2_package2_H_
#define _example2_package2_H_

#include "kcg_types.h"
#include "example1_package1.h"

/* ========================  input structure  ====================== */
typedef struct { kcg_int32 /* x/ */ x; } inC_example2_package2;

/* =====================  no output structure  ====================== */

/* ========================  context type  ========================= */
typedef struct {
  /* ---------------------------  outputs  --------------------------- */
  kcg_int32 /* y/ */ y;
  /* -----------------------  no local probes  ----------------------- */
  /* -----------------------  no local memory  ----------------------- */
  /* -------------------- no sub nodes' contexts  -------------------- */
  /* ----------------- no clocks of observable data ------------------ */
} outC_example2_package2;

/* ===========  node initialization and cycle functions  =========== */
/* package2::example2/ */
extern void example2_package2(
  inC_example2_package2 *inC,
  outC_example2_package2 *outC);

#ifndef KCG_NO_EXTERN_CALL_TO_RESET
extern void example2_reset_package2(outC_example2_package2 *outC);
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */

#ifndef KCG_USER_DEFINED_INIT
extern void example2_init_package2(outC_example2_package2 *outC);
#endif /* KCG_USER_DEFINED_INIT */



#endif /* _example2_package2_H_ */
/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** example2_package2.h
** Generation date: 2023-09-09T15:48:40
*************************************************************$ */

