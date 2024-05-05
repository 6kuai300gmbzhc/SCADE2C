#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "test7.h"
void test7(inC_test7 *inC, outC_test7 *outC)
{
outC->out1=inC->in1+kcg_lit_int8(1);

}
void test7_init(outC_test7 *outC)
{
outC->out1=kcg_lit_int8(0);
}
void test7_reset(outC_test7 *outC)
{
}
