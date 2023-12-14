_activate2_H_
#define _activate2_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in1;
kcg_int32 in2;
color2 in3;
} inC_activate2;


typedef struct {
kcg_int32 mem_pre;
kcg_int32 mem_pre1;
kcg_bool init;
kcg_bool init1;
kcg_bool init2;
kcg_int32 fbyIdx;
kcg_int32 fbyArray;
kcg_bool init3;
kcg_int32 fbyIdx1;
kcg_int32 fbyArray1;
kcg_int32 out1;
kcg_int32 out2;
kcg_int32 fbyIdx;
kcg_int32 fbyArray[5];
kcg_int32 fbyIdx1;
kcg_int32 fbyArray1[5];
} outC_activate2;

extern void activate2(inC_activate2 *inC, outC_activate2 *outC);

extern void activate2_reset(outC_activate2 *outC);

extern void activate2_init(outC_activate2 *outC);
