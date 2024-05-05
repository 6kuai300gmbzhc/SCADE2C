#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "case_test.h"
void case_test(inC_case_test *inC, outC_case_test *outC)
{
kcg_bool caseTmp;
switch(inC->in4){
case TT :
{
caseTmp = inC->in1;
break;
}
case FF :
{
caseTmp = inC->in2;
break;
}
default :
{
caseTmp = inC->in3;
break;
}
outC->out1 = caseTmp;

}
void case_test_init(outC_case_test *outC)
{
outC->out1=kcg_true;
}
void case_test_reset(outC_case_test *outC)
{
}
