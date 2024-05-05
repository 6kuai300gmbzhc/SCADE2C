#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testPara.h"
void testPara(inC_testPara *inC, outC_testPara *outC)
{
kcg_float32 lastTmp=outC->out2;
kcg_float32 lastTmp1=outC->out3;
outC->out2=inC->in2;
outC->out3=lastTmp;
outC->out4=lastTmp1;

}
void testPara_init(outC_testPara *outC)
{
outC->out2=kcg_lit_float32(0.5);
outC->out3=kcg_lit_float32(0.5);
outC->out4=kcg_lit_float32(0.0);
}
void testPara_reset(outC_testPara *outC)
{
}
