/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-09T15:48:40
*************************************************************$ */

#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "example2_package2.h"

/* package2::example2/ */
void example2_package2(inC_example2_package2 *inC, outC_example2_package2 *outC)
{
  outC->y = /* y=(package1::example1)/ */ example1_package1(inC->x, inC->x);
}

#ifndef KCG_USER_DEFINED_INIT
void example2_init_package2(outC_example2_package2 *outC)
{
  outC->y = kcg_lit_int32(0);
}
#endif /* KCG_USER_DEFINED_INIT */


#ifndef KCG_NO_EXTERN_CALL_TO_RESET
void example2_reset_package2(outC_example2_package2 *outC)
{
}
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */



/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** example2_package2.c
** Generation date: 2023-09-09T15:48:40
*************************************************************$ */

