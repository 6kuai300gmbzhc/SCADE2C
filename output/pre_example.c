#include"kcg_consts.h"
#include"kcg_sensors.h"
#include "pre_example.h"
void pre_example(inC_pre_example *inC, outC_pre_example *outC)
{

}
void pre_example_init(outC_pre_example *outC)
{
outC->output1=kcg_lit_int32(0);
outC->output2=kcg_lit_int32(0);
}
void pre_example_reset(outC_pre_example *outC)
{
}
