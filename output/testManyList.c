#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testManyList.h"
void testManyList(inC_testManyList *inC, outC_testManyList *outC)
{
outC->out1=inC->in1.tt1;
outC->out2=(inC->in1.tt2.tt4+inC->in1.tt2.tt5);

}
void testManyList_init(outC_testManyList *outC)
{
outC->out1=kcg_lit_int8(0);
outC->out2=kcg_lit_float32(0.0);
}
void testManyList_reset(outC_testManyList *outC)
{
}
