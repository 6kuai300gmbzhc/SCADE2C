#ifndef _vwtovr_H_
#define _vwtovr_H_
#include "kcg_types.h"

typedef struct {
kcg_float64 vw;
} inC_vwtovr;


typedef struct {
kcg_float64 vr;
kcg_bool init;
kcg_float64 mem_pre;
} outC_vwtovr;

extern void vwtovr(inC_vwtovr *inC, outC_vwtovr *outC);

extern void vwtovr_reset(outC_vwtovr *outC);

extern void vwtovr_init(outC_vwtovr *outC);
#endif