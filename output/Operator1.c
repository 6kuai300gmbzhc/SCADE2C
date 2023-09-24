#include"kcg_consts.h"
#include"kcg_sensors.h"
#include "Operator1.h"
void Operator1(inC_Operator1 *inC, outC_Operator1 *outC)
{
outC->Output1 = Sensor1 + Sensor2;
}
void Operator1_init(outC_Operator1 *outC)
{
}
void Operator1_reset(outC_Operator1 *outC)
{
}
