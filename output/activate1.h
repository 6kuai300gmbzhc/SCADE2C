_activate1_H_
#define _activate1_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in1;
kcg_int32 in2;
} inC_activate1;


typedef struct {
kcg_int32 mem_pre;
kcg_bool init;
kcg_bool init1;
kcg_int32 fbyIdx;
kcg_int32 fbyArray;
kcg_int32 out1;
} outC_activate1;

extern void activate1(inC_activate1 *inC, outC_activate1 *outC);

extern void activate1_reset(outC_activate1 *outC);

extern void activate1_init(outC_activate1 *outC);
