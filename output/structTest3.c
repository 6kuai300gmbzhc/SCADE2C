#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "structTest3.h"
void structTest3(inC_structTest3 *inC, outC_structTest3 *outC)
{
outC->out1.tt1 = inC->in1;
outC->out1.tt2 = inC->in2;
outC->out1.tt3.tt1 = inC->in3;
memcpy(&outC->out2,&outC->out1.tt3,sizeof(type4));
outC->out3 = outC->out1.tt2;
outC->out4.tt1 = (inC->in1+kcg_lit_int8(1));
outC->out4.tt2 = inC->in2;
memcpy(&outC->out4.tt3,&outC->out1.tt3,sizeof(type4));

}
void structTest3_init(outC_structTest3 *outC)
{
outC->out1.tt1=kcg_lit_int8(0);
outC->out1.tt2=kcg_true;
outC->out1.tt3.tt1=kcg_lit_float32(0.0);
outC->out4.tt1=kcg_lit_int8(0);
outC->out4.tt2=kcg_true;
outC->out4.tt3.tt1=kcg_lit_float32(0.0);
outC->out2.tt1=kcg_lit_float32(0.0);
outC->out3=kcg_true;
}
void structTest3_reset(outC_structTest3 *outC)
{
}
