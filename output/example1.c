#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "example1.h"
void example1(inC_example1 *inC, outC_example1 *outC)
{
outC->z=inC->x+inC->y;

}
void example1_init(outC_example1 *outC)
{
outC->z=kcg_lit_int32(0);
}
void example1_reset(outC_example1 *outC)
{
}
