#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "arrayStructTest1.h"
void arrayStructTest1(inC_arrayStructTest1 *inC, outC_arrayStructTest1 *outC)
{
outC->o3 = outC->o1[kcg_lit_int8(0)].tt1;

}
void arrayStructTest1_init(outC_arrayStructTest1 *outC)
{
for(kcg_size idx0=0;idx0<3;idx0++){
outC->o1[idx0].tt1=kcg_lit_int8(0);
outC->o1[idx0].tt2=kcg_true;
}
for(kcg_size idx0=0;idx0<3;idx0++){
outC->o2[idx0].tt1=kcg_lit_int8(0);
outC->o2[idx0].tt2=kcg_true;
}
outC->o3=kcg_lit_int8(0);
}
void arrayStructTest1_reset(outC_arrayStructTest1 *outC)
{
}
