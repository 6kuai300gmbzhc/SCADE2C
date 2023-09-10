#include"kcg_consts.h"
#include"kcg_sensors.h"
#include "plus_two.h"
void plus_two(inC_plus_two *inC, outC_plus_two *outC)
{
outC->y = inC->x + kcg_lit_int8(2);
}
void plus_two_init(outC_plus_two *outC)
{
}
void plus_two_reset(outC_plus_two *outC)
{
}
