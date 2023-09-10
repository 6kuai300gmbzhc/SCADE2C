/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** Command: kcg662.exe -config D:/scade_pro/lab_test/KCG/config.txt
** Generation date: 2023-09-09T16:30:46
*************************************************************$ */

#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "example1_package1.h"

/* package1::example1/ */
void example1_package1(inC_example1_package1 *inC, outC_example1_package1 *outC)
{
  outC->z = inC->x + inC->y;
}

#ifndef KCG_USER_DEFINED_INIT
void example1_init_package1(outC_example1_package1 *outC)
{
  outC->z = kcg_lit_int32(0);
}
#endif /* KCG_USER_DEFINED_INIT */


#ifndef KCG_NO_EXTERN_CALL_TO_RESET
void example1_reset_package1(outC_example1_package1 *outC)
{
}
#endif /* KCG_NO_EXTERN_CALL_TO_RESET */



/* $********** SCADE Suite KCG 32-bit 6.6.2 (build i4) **********
** example1_package1.c
** Generation date: 2023-09-09T16:30:46
*************************************************************$ */

