/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-09T16:30:46
*************************************************************$ */
#ifndef _example1_package1_H_
#define _example1_package1_H_

#include "kcg_types.h"

/* ========================  input structure  ====================== */
typedef struct {
  kcg_int32 /* x/ */ x;
  kcg_int32 /* y/ */ y;
} inC_example1_package1;

/* =====================  no output structure  ====================== */

/* ========================  context type  ========================= */
typedef struct {
  /* ---------------------------  outputs  --------------------------- */
  kcg_int32 /* z/ */ z;
  /* -----------------------  no local probes  ----------------------- */
  /* -----------------------  no local memory  ----------------------- */
  /* -------------------- no sub nodes' contexts  -------------------- */
  /* ----------------- no clocks of observable data ------------------ */
} outC_example1_package1;

/* ===========  node initialization and cycle functions  =========== */
/* package1::example1/ */
extern void example1_package1(
  inC_example1_package1 *inC,
  outC_example1_package1 *outC);

#ifndef KCG_NO_EXTERN_CALL_TO_RESET
extern void example1_reset_package1(outC_example1_package1 *outC);
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */

#ifndef KCG_USER_DEFINED_INIT
extern void example1_init_package1(outC_example1_package1 *outC);
#endif /* KCG_USER_DEFINED_INIT */



#endif /* _example1_package1_H_ */
/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** example1_package1.h
** Generation date: 2023-09-09T16:30:46
*************************************************************$ */

