#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "Square.h"
kcg_float64 Square(kcg_float64 Square_In)
{
kcg_float64 Square_Out;
kcg_float64 _L1;
kcg_float64 _L2;
_L1 = Square_In;
_L2 = (_L1*_L1);
Square_Out = _L2;
return Square_Out;

}
