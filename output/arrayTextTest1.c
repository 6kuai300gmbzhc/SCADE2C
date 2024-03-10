#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "arrayTextTest1.h"
void arrayTextTest1(inC_arrayTextTest1 *inC, outC_arrayTextTest1 *outC)
{
outC->o1[0] = inC->in1;
outC->o1[1] = inC->in2;
outC->o1[2] = inC->in3;
outC->o3 = outC->o1[kcg_lit_int8(1)];

}
void arrayTextTest1_init(outC_arrayTextTest1 *outC)
{
for(kcg_size idx0=0;idx0<3;idx0++){
outC->o1[idx0]=kcg_lit_int8(0);
}
outC->o3=kcg_lit_int8(0);
}
void arrayTextTest1_reset(outC_arrayTextTest1 *outC)
{
}
