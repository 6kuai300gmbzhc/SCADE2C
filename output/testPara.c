#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testPara.h"
void testPara(inC_testPara *inC, outC_testPara *outC)
{
outC->out1=kcg_lit_int32(1);
outC->out2=inC->in2;
outC->out3=outC->mem_last;
outC->mem_last=outC->out2;
outC->out4=outC->mem_last1;
outC->mem_last1=outC->out3;

}
void testPara_init(outC_testPara *outC)
{
outC->mem_last=kcg_lit_float32(0.0);
outC->mem_last1=kcg_lit_float32(0.0);
outC->out1=kcg_lit_int32(0);
outC->out2=kcg_lit_float32(0.5);
outC->out3=kcg_lit_float32(0.5);
outC->out4=kcg_lit_float32(0.0);
}
void testPara_reset(outC_testPara *outC)
{
}
