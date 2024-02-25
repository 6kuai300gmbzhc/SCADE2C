#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "PFD.h"
void PFD(inC_PFD *inC, outC_PFD *outC)
{
kcg_int32 counter;
kcg_float32 counter_f;
kcg_int32 counter2;
kcg_bool dire;
kcg_float32 counter2_f;
kcg_bool _L118;
kcg_int32 _L120;
kcg_int32 _L121;
kcg_int32 _L122;
kcg_float32 _L125;
kcg_int32 _L126;
kcg_float32 _L127;
kcg_float32 _L128;
kcg_float32 _L129;
kcg_float32 _L130;
kcg_float32 _L131;
kcg_float32 _L132;
kcg_float32 _L133;
kcg_float32 _L134;
kcg_float32 _L135;
kcg_float32 _L136;
kcg_bool _L137;
kcg_int32 _L138;
kcg_bool _L139;
kcg_int32 _L140;
kcg_int32 _L141;
kcg_int32 _L142;
kcg_int32 _L143;
kcg_bool _L144;
kcg_bool _L145;
kcg_bool _L146;
kcg_bool _L147;
kcg_bool _L148;
kcg_bool _L149;
kcg_bool _L150;
kcg_bool _L151;
kcg_int32 _L152;
kcg_int32 _L153;
kcg_int32 _L154;
kcg_int32 _L156;
kcg_float32 _L157;
kcg_float32 _L158;
kcg_bool _L159;
kcg_int32 _L161;
kcg_float32 _L162;
kcg_int32 _L163;
kcg_float32 _L164;
kcg_bool _L165;
kcg_float32 _L166;
kcg_float32 _L167;
kcg_float32 _L169;
kcg_float32 _L173;
kcg_float32 _L174;
kcg_bool _L177;
kcg_float32 _L178;
kcg_float32 _L180;
kcg_float32 _L181;
kcg_float32 _L182;
kcg_float32 _L184;
kcg_int32 lastTmp=outC->counter;
kcg_int32 ifTmp;
kcg_int32 lastTmp1=outC->counter;
kcg_int32 ifTmp1;
kcg_int32 lastTmp2=outC->AttentionGettingBox;
kcg_int32 ifTmp2;
kcg_int32 lastTmp3=outC->AttentionGettingBox;
kcg_int32 lastTmp4=outC->counter2;
kcg_bool lastTmp5=outC->dire;
kcg_bool ifTmp3;
kcg_bool lastTmp6=outC->dire;
kcg_int32 lastTmp7=outC->counter2;
kcg_bool lastTmp8=outC->dire;
kcg_bool ifTmp4;
kcg_bool lastTmp9=outC->dire;
kcg_bool lastTmp10=outC->dire;
kcg_int32 ifTmp5;
kcg_int32 lastTmp11=outC->counter2;
kcg_int32 lastTmp12=outC->counter2;
_L118 = ((lastTmp+kcg_lit_int32(1))>kcg_lit_int32(25000));
_L121 = kcg_lit_int32(0);
_L122 = (lastTmp1+kcg_lit_int32(1));
_L139 = (lastTmp2==kcg_lit_int32(1));
_L141 = kcg_lit_int32(2);
_L142 = kcg_lit_int32(1);
_L143 = lastTmp3;
_L144 = (((lastTmp4+kcg_lit_int32(1))>kcg_lit_int32(100)) & lastTmp5);
_L146 = !lastTmp6;
_L147 = (((lastTmp7-kcg_lit_int32(1))<(-kcg_lit_int32(100))) & (lastTmp8==kcg_false));
_L149 = !lastTmp9;
_L150 = lastTmp10;
_L153 = (lastTmp11+kcg_lit_int32(1));
_L154 = (lastTmp12-kcg_lit_int32(1));
_L159 = kcg_true;
outC->RollAngleState = _L159;
outC->AirSpeedState = _L159;
_L161 = kcg_lit_int32(1);
_L163 = kcg_lit_int32(1);
_L165 = kcg_true;
_L173 = kcg_lit_float32(0.5);
_L174 = kcg_lit_float32(18.0);
_L177 = kcg_true;
_L180 = kcg_lit_float32(5000.0);
outC->PressureAltitudeState = _L163;
outC->MachNumberValue = _L173;
if(_L118)
{
ifTmp = _L121;
}
else{
ifTmp = _L122;
}
_L120 = ifTmp;
if(_L139)
{
ifTmp2 = _L141;
}
else{
ifTmp2 = _L142;
}
_L140 = ifTmp2;
if(_L147)
{
ifTmp4 = _L149;
}
else{
ifTmp4 = _L150;
}
_L148 = ifTmp4;
outC->PitchAngleState = _L159;
outC->Language = _L161;
outC->CourseState = _L165;
outC->Temprature = _L174;
outC->LateralAccelerationState = _L177;
outC->StandardPressureAltitudeValue = _L180;
outC->counter = _L120;
_L126 = outC->counter;
_L127 = (kcg_float32)_L126;
_L137 = ((outC->counter % kcg_lit_int32(100))==kcg_lit_int32(0));
if(_L137)
{
ifTmp1 = _L140;
}
else{
ifTmp1 = _L143;
}
_L138 = ifTmp1;
if(_L144)
{
ifTmp3 = _L146;
}
else{
ifTmp3 = _L148;
}
_L145 = ifTmp3;
outC->dire = _L145;
_L151 = outC->dire;
if(_L151)
{
ifTmp5 = _L153;
}
else{
ifTmp5 = _L154;
}
_L152 = ifTmp5;
outC->AttentionGettingBox = _L138;
counter_f = _L127;
_L128 = counter_f;
_L129 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(90.0));
_L130 = (kcg_lit_float32(25.0)-((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(25.0)));
_L131 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(2000.0));
_L132 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(300.0));
_L133 = (counter_f/kcg_lit_float32(25000.0));
_L134 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(0.9));
_L135 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(0.8));
_L136 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(100.0));
outC->counter2 = _L152;
_L156 = outC->counter2;
_L157 = (kcg_float32)_L156;
counter2_f = _L157;
_L158 = (counter2_f/kcg_lit_float32(5.0));
outC->RollAngle = _L158;
_L162 = (counter2_f+kcg_lit_float32(100.0));
_L164 = ((counter2_f+kcg_lit_float32(100.0))*kcg_lit_float32(50.0));
_L166 = ((counter2_f+kcg_lit_float32(100.0))*kcg_lit_float32(1.8));
outC->CourseAngle = _L166;
_L167 = counter2_f;
_L169 = (counter2_f/kcg_lit_float32(20.0));
_L178 = (counter2_f+kcg_lit_float32(100.0));
outC->TrueAirSpeedValue = _L178;
_L181 = ((counter2_f+kcg_lit_float32(100.0))*kcg_lit_float32(0.9));
_L182 = ((counter2_f+kcg_lit_float32(100.0))*kcg_lit_float32(0.1));
_L184 = ((counter2_f+kcg_lit_float32(100.0))*kcg_lit_float32(0.9));
outC->FuelFlow = _L128;
outC->N3 = _L129;
outC->OilQuantity = _L130;
outC->OilTemperature = _L131;
outC->OilPressure = _L132;
outC->N1Vibrations = _L133;
outC->N2Vibrations = _L134;
outC->N3Vibrations = _L135;
outC->StartingSenquenceIndication = _L136;
_L125 = ((counter_f/kcg_lit_float32(25000.0))*kcg_lit_float32(100.0));
outC->PitchAngle = _L158;
outC->AirSpeedValue = _L162;
outC->AltitudeValue = _L164;
outC->ShouldFlyCourseAngle = _L166;
outC->TurnRateValue = _L167;
outC->VertSpeedValue = _L169;
outC->GroundSpeedValue = _L178;
outC->WindDirAngle = _L181;
outC->WindSpeedValue = _L182;
outC->CRSAngle = _L184;
outC->N2 = _L125;

}
void PFD_init(outC_PFD *outC)
{
outC->counter=kcg_lit_int32(0);
outC->counter2=kcg_lit_int32(0);
outC->dire=kcg_true;
outC->WindDirAngle=kcg_lit_float32(0.0);
outC->WindSpeedValue=kcg_lit_float32(0.0);
outC->StandardPressureAltitudeValue=kcg_lit_float32(0.0);
outC->TrueAirSpeedValue=kcg_lit_float32(0.0);
outC->GroundSpeedValue=kcg_lit_float32(0.0);
outC->LateralAccelerationState=kcg_true;
outC->Temprature=kcg_lit_float32(0.0);
outC->MachNumberValue=kcg_lit_float32(0.0);
outC->VertSpeedValue=kcg_lit_float32(0.0);
outC->TurnRateValue=kcg_lit_float32(0.0);
outC->CourseAngle=kcg_lit_float32(0.0);
outC->ShouldFlyCourseAngle=kcg_lit_float32(0.0);
outC->CourseState=kcg_true;
outC->AltitudeValue=kcg_lit_float32(0.0);
outC->PressureAltitudeState=kcg_lit_int32(0);
outC->AirSpeedValue=kcg_lit_float32(0.0);
outC->Language=kcg_lit_int32(1);
outC->AirSpeedState=kcg_false;
outC->RollAngle=kcg_lit_float32(0.0);
outC->PitchAngle=kcg_lit_float32(0.0);
outC->CRSAngle=kcg_lit_float32(0.0);
outC->PitchAngleState=kcg_true;
outC->RollAngleState=kcg_true;
outC->FuelFlow=kcg_lit_float32(0.0);
outC->N2=kcg_lit_float32(0.0);
outC->N3=kcg_lit_float32(0.0);
outC->OilQuantity=kcg_lit_float32(0.0);
outC->OilTemperature=kcg_lit_float32(0.0);
outC->OilPressure=kcg_lit_float32(0.0);
outC->N1Vibrations=kcg_lit_float32(0.0);
outC->N2Vibrations=kcg_lit_float32(0.0);
outC->N3Vibrations=kcg_lit_float32(0.0);
outC->StartingSenquenceIndication=kcg_lit_float32(0.0);
outC->AttentionGettingBox=kcg_lit_int32(1);
}
void PFD_reset(outC_PFD *outC)
{
}
