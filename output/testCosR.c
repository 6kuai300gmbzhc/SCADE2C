#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "testCosR.h"
#include "Square.h"
void testCosR(inC_testCosR *inC, outC_testCosR *outC)
{
outC->y=Square(inC->x);

}
void testCosR_init(outC_testCosR *outC)
{
outC->y=kcg_lit_float64(0.0);
}
void testCosR_reset(outC_testCosR *outC)
{
}
