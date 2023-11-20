_NNN_H_
#define _NNN_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 x;
kcg_int32 y;
kcg_bool tmp;
} inC_NNN;


typedef struct {
kcg_bool tmp2;
} outC_NNN;

extern void NNN(inC_NNN *inC, outC_NNN *outC);

extern void NNN_reset(outC_NNN *outC);

extern void NNN_init(outC_NNN *outC);
