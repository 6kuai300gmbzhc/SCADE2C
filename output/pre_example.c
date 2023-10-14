#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "pre_example.h"
void pre_example(inC_pre_example *inC, outC_pre_example *outC)
{
outC->output2 = inC->input1 + inC->input2;
outC->output1 =  (outC-> init )  ? kcg_lit_int32(1) :  ( mem_pre ) ;
outC->init=kcg_false;
outC->mem_pre=kcg_lit_(3);

}
void pre_example_init(outC_pre_example *outC)
{
outC->mem_pre=kcg_lit_int32(0);
outC->output1=kcg_lit_int32(0);
outC->output2=kcg_lit_int32(0);
outC->init=kcg_true;
}
void pre_example_reset(outC_pre_example *outC)
{
outC->init=kcg_true;
outC->mem_pre=kcg_lit_int32(0);
}
