#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testInputLast.h"
void testInputLast(inC_testInputLast *inC, outC_testInputLast *outC)
{
outC->out1=(inC->in1+kcg_lit_int8(1));

}
void testInputLast_init(outC_testInputLast *outC)
{
outC->in1=kcg_lit_int8(0);
outC->out1=kcg_lit_int8(0);
}
void testInputLast_reset(outC_testInputLast *outC)
{
}
