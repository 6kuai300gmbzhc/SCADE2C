_activateIf_H_
#define _activateIf_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in1;
kcg_int32 in2;
} inC_activateIf;


typedef struct {
kcg_bool init;
kcg_int32 out;
kcg_int32 fbyIdx;
kcg_int32 fbyArray[5];
} outC_activateIf;

extern void activateIf(inC_activateIf *inC, outC_activateIf *outC);

extern void activateIf_reset(outC_activateIf *outC);

extern void activateIf_init(outC_activateIf *outC);
