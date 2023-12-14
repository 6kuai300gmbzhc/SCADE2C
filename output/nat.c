#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "nat.h"
void nat(inC_nat *inC, outC_nat *outC)
{
kcg_uint64 initElem;
if(outC->init){
initElem=inC->in;
outC->init=kcg_false;
}else{
initElem=inC->in+outC->mem_pre;
}
outC->n=initElem;
outC->mem_pre=outC->n;

}
void nat_init(outC_nat *outC)
{
outC->mem_pre=kcg_lit_uint64(0);
outC->init=kcg_true;
outC->n=kcg_lit_uint64(0);
}
void nat_reset(outC_nat *outC)
{
outC->mem_pre=kcg_lit_uint64(0);
}
