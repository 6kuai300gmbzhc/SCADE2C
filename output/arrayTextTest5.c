#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "arrayTextTest5.h"
void arrayTextTest5(inC_arrayTextTest5 *inC, outC_arrayTextTest5 *outC)
{
memcpy(&outC->o1,&inC->in1,sizeof(int8));

}
void arrayTextTest5_init(outC_arrayTextTest5 *outC)
{
for(kcg_size idx2=0;idx2<2;idx2++){
for(kcg_size idx1=0;idx1<3;idx1++){
for(kcg_size idx0=0;idx0<4;idx0++){
outC->o1[idx2][idx1][idx0]=kcg_lit_int8(0);
}
}
}
}
void arrayTextTest5_reset(outC_arrayTextTest5 *outC)
{
}
