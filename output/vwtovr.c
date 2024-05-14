#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "macro_libmathext64.h"
#include "vwtovr.h"
void vwtovr(kcg_float64 vw,outC_vwtovr *outC)
{
kcg_float64 _L1;
kcg_float64 _L2;
kcg_float64 _L3;
kcg_float64 _L4;
kcg_float64 _L5;
kcg_float64 _L6;
kcg_bool _L8;
kcg_float64 initTmp;
kcg_float64 tmp_pre=outC->mem_pre;
kcg_float64 ifTmp;
_L2 = tmp_pre;
_L4 = kcg_lit_float64(0.09);
_L6 = vw;
if(outC->init){
initTmp = kcg_lit_float64(70);
}else{
initTmp = _L2;
}
_L1 = initTmp;
_L3 = (_L1-_L4);
_L8 = (_L3<_L6);
if(_L8){
ifTmp = _L6;
}else{
ifTmp = _L3;
}
_L5 = ifTmp;
outC->vr = _L5;
outC->mem_pre = _L5;

}
void vwtovr_init(outC_vwtovr *outC)
{
outC->vr=kcg_lit_float64(70);
outC->init=kcg_true;
outC->mem_pre=kcg_lit_float64(0.0);
}
void vwtovr_reset(outC_vwtovr *outC)
{
outC->mem_pre = kcg_lit_float64(0.0);
}
