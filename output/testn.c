#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "testn.h"
void testn(inC_testn *inC, outC_testn *outC)
{
outC->y = inC->x1+inC->x2;

}
void testn_init(outC_testn *outC)
{
outC->y=kcg_lit_int32(0);
}
void testn_reset(outC_testn *outC)
{
}
