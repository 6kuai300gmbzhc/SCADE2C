#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testStruct.h"
void testStruct(inC_testStruct *inC, outC_testStruct *outC)
{
outC->out1 = (inC->in1.tt2.tt4+inC->in1.tt2.tt5);

}
void testStruct_init(outC_testStruct *outC)
{
outC->out1=kcg_lit_float32(0.0);
}
void testStruct_reset(outC_testStruct *outC)
{
}
