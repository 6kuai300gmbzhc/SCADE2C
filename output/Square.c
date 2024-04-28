#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "Square.h"
void Square(kcg_float64 in1,kcg_float64 in2,kcg_float64 *out1,kcg_float64 *out2)
{
kcg_float64 _L1;
kcg_float64 _L2;
_L1 = (in1+in2);
_L2 = (_L1*_L1);
*out1 = _L2;
*out2 = _L1;

}
void Square_init(outC_Square *outC)
{
outC->out1=kcg_lit_float64(0.0);
outC->out2=kcg_lit_float64(0.0);
}
void Square_reset(outC_Square *outC)
{
}
