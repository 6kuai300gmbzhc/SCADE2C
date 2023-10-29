#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "bool_expr.h"
void bool_expr(inC_bool_expr *inC, outC_bool_expr *outC)
{
outC->out2=inC->in1 ^ inC->in2;
outC->out3=(inC->in1)+(inC->in2)+(inC->in3)<=1;

}
void bool_expr_init(outC_bool_expr *outC)
{
outC->out1=kcg_true;
outC->out2=kcg_true;
outC->out3=kcg_true;
}
void bool_expr_reset(outC_bool_expr *outC)
{
}
