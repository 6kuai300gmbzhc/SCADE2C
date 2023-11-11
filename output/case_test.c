#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "case_test.h"
void case_test(inC_case_test *inC, outC_case_test *outC)
{
switch(inC->in4){
case 'a' :
caseTmp = inC->in1;
break;
case 'b' :
caseTmp = inC->in2;
break;
default  :
caseTmp = inC->in3;
break;
}
switch(inC->in4){
case 'a' :
caseTmp1 = inC->in2;
break;
case 'b' :
caseTmp1 = inC->in3;
break;
default  :
caseTmp1 = inC->in1;
break;
}
outC->out1=caseTmp;
outC->out2=caseTmp1;

}
void case_test_init(outC_case_test *outC)
{
outC->out1=kcg_lit_int8(0);
outC->out2=kcg_lit_int8(0);
}
void case_test_reset(outC_case_test *outC)
{
}
