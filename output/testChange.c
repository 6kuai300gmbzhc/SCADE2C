#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testChange.h"
void testChange(inC_testChange *inC, outC_testChange *outC)
{
outC->out1=(kcg_float64)(inC->in1+kcg_lit_float64(1))+kcg_lit_float64(2);

}
void testChange_init(outC_testChange *outC)
{
outC->out1=kcg_lit_float64(0.0);
}
void testChange_reset(outC_testChange *outC)
{
}
