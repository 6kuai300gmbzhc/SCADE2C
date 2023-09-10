/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-10T21:54:08
*************************************************************$ */

#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "N.h"

/* N/ */
void N(inC_N *inC, outC_N *outC)
{
  outC->o1 = /* o1=(f)/ */ f_10(&inC->a1);
}

#ifndef KCG_USER_DEFINED_INIT
void N_init(outC_N *outC)
{
  outC->o1 = kcg_lit_int32(0);
}
#endif /* KCG_USER_DEFINED_INIT */


#ifndef KCG_NO_EXTERN_CALL_TO_RESET
void N_reset(outC_N *outC)
{
}
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */



/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** N.c
** Generation date: 2023-09-10T21:54:08
*************************************************************$ */

