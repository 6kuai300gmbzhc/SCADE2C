#ifndef _PFD_H_
#define _PFD_H_
#include "kcg_types.h"

typedef struct {
} inC_PFD;


typedef struct {
kcg_int32 counter;
kcg_int32 counter2;
kcg_bool dire;
kcg_float32 WindDirAngle;
kcg_float32 WindSpeedValue;
kcg_float32 StandardPressureAltitudeValue;
kcg_float32 TrueAirSpeedValue;
kcg_float32 GroundSpeedValue;
kcg_bool LateralAccelerationState;
kcg_float32 Temprature;
kcg_float32 MachNumberValue;
kcg_float32 VertSpeedValue;
kcg_float32 TurnRateValue;
kcg_float32 CourseAngle;
kcg_float32 ShouldFlyCourseAngle;
kcg_bool CourseState;
kcg_float32 AltitudeValue;
kcg_int32 PressureAltitudeState;
kcg_float32 AirSpeedValue;
kcg_int32 Language;
kcg_bool AirSpeedState;
kcg_float32 RollAngle;
kcg_float32 PitchAngle;
kcg_float32 CRSAngle;
kcg_bool PitchAngleState;
kcg_bool RollAngleState;
kcg_float32 FuelFlow;
kcg_float32 N2;
kcg_float32 N3;
kcg_float32 OilQuantity;
kcg_float32 OilTemperature;
kcg_float32 OilPressure;
kcg_float32 N1Vibrations;
kcg_float32 N2Vibrations;
kcg_float32 N3Vibrations;
kcg_float32 StartingSenquenceIndication;
kcg_int32 AttentionGettingBox;
} outC_PFD;

extern void PFD(inC_PFD *inC, outC_PFD *outC);

extern void PFD_reset(outC_PFD *outC);

extern void PFD_init(outC_PFD *outC);
#endif