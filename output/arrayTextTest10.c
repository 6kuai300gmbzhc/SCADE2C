#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "arrayTextTest10.h"
void arrayTextTest10(inC_arrayTextTest10 *inC, outC_arrayTextTest10 *outC)
{
outC->o1.tt1[0] = inC->in1;
outC->o1.tt1[1] = inC->in2;

}
void arrayTextTest10_init(outC_arrayTextTest10 *outC)
{
outC->o1.tt1=kcg_lit_int8(0);
}
void arrayTextTest10_reset(outC_arrayTextTest10 *outC)
{
}
