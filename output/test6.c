#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "test6.h"
void test6(inC_test6 *inC, outC_test6 *outC)
{
outC->out2.tt1=kcg_lit_int8(8);
outC->out2.tt2.tt3=kcg_false;
outC->out1.tt1=inC->in1+kcg_lit_int8(1);
memcpy(&outC->out1.tt2,&outC->out3,sizeof(tmpStruct1));
memcpy(&outC->out3,&inC->in3,sizeof(type12));

}
void test6_init(outC_test6 *outC)
{
outC->out1.tt1=kcg_lit_int8(0);
outC->out1.tt2.tt3=kcg_true;
outC->out2.tt1=kcg_lit_int8(0);
outC->out2.tt2.tt3=kcg_true;
outC->out3.tt3=kcg_true;
}
void test6_reset(outC_test6 *outC)
{
}
