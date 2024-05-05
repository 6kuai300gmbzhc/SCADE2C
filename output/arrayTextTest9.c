#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "arrayTextTest9.h"
void arrayTextTest9(inC_arrayTextTest9 *inC, outC_arrayTextTest9 *outC)
{
outC->o2 = (inC->in1+inC->in2);
outC->o1[0][0].tt1 = outC->o2;
outC->o1[0][0].tt2 = inC->in3;
memcpy(&outC->o1[0][1],&inC->in5,sizeof(struct5));
memcpy(&outC->o1[1][0],&inC->in5,sizeof(struct5));
memcpy(&outC->o1[1][1],&inC->in6,sizeof(struct5));
memcpy(&outC->o1[2][0],&inC->in6,sizeof(struct5));
outC->o1[2][1].tt1 = inC->in2;
outC->o1[2][1].tt2 = inC->in4;

}
void arrayTextTest9_init(outC_arrayTextTest9 *outC)
{
for(kcg_size idx1=0;idx1<2;idx1++){
for(kcg_size idx0=0;idx0<3;idx0++){
outC->o1[idx1][idx0].tt1=kcg_lit_int8(0);
outC->o1[idx1][idx0].tt2=kcg_true;
}
}
outC->o2=kcg_lit_int8(0);
}
void arrayTextTest9_reset(outC_arrayTextTest9 *outC)
{
}
