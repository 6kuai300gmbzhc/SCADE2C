/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-09T16:00:05
*************************************************************$ */

#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "example3_package3.h"

/* package3::example3/ */
void example3_package3(inC_example3_package3 *inC, outC_example3_package3 *outC)
{
  outC->y = kcg_lit_int32(2);
}

#ifndef KCG_USER_DEFINED_INIT
void example3_init_package3(outC_example3_package3 *outC)
{
  outC->y = kcg_lit_int32(0);
}
#endif /* KCG_USER_DEFINED_INIT */


#ifndef KCG_NO_EXTERN_CALL_TO_RESET
void example3_reset_package3(outC_example3_package3 *outC)
{
}
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */



/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** example3_package3.c
** Generation date: 2023-09-09T16:00:05
*************************************************************$ */

