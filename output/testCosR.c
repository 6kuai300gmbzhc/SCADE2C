#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "testCosR.h"
#include "Square.h"
void testCosR(inC_testCosR *inC, outC_testCosR *outC)
{
Square(inC->x,inC->y,&outC->y1,&outC->y2);

}
void testCosR_init(outC_testCosR *outC)
{
outC->y1=kcg_lit_float64(0.0);
outC->y2=kcg_lit_float64(0.0);
}
void testCosR_reset(outC_testCosR *outC)
{
}
