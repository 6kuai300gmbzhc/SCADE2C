#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "order_list.h"
void order_list(inC_order_list *inC, outC_order_list *outC)
{
kcg_int8 tmp;
tmp=inC->in1-inC->in2;
outC->out1=tmp+inC->in1;

}
void order_list_init(outC_order_list *outC)
{
outC->out1=kcg_lit_int8(0);
}
void order_list_reset(outC_order_list *outC)
{
}
