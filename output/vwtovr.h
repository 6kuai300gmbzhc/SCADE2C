#ifndef _vwtovr_H_
#define _vwtovr_H_
#include "kcg_types.h"


typedef struct {
kcg_float64 vr;
kcg_bool init;
kcg_float64 mem_pre;
} outC_vwtovr;
extern void vwtovr(kcg_float64 vw,outC_vwtovr *outC);

extern void vwtovr_reset(outC_vwtovr *outC);

extern void vwtovr_init(outC_vwtovr *outC);
#endif
