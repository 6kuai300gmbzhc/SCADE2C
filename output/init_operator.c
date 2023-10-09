#include"kcg_consts.h"
#include"kcg_sensors.h"
#include "init_operator.h"
void init_operator(inC_init_operator *inC, outC_init_operator *outC)
{
outC->output1 =  (out->init)  ? kcg_lit_int8(0) : inC->input1 ;
outC->init=kcg_false ;
}
void init_operator_init(outC_init_operator *outC)
{
outC->output1=kcg_lit_int8(0);
outC->init=kcg_true;
}
void init_operator_reset(outC_init_operator *outC)
{
outC->init=kcg_true;
}
