#ifndef _testControlBlockIf_H_
#define _testControlBlockIf_H_
#include "kcg_types.h"

typedef struct {
kcg_float32 in1;
kcg_float32 in2;
kcg_float32 in5;
kcg_int32 in3;
kcg_int32 in4;
} inC_testControlBlockIf;


typedef struct {
kcg_bool init;
kcg_int32 out2;
kcg_int32 out3;
kcg_int32 fbyIdx;
kcg_int32 fbyArray[5];
} outC_testControlBlockIf;

extern void testControlBlockIf(inC_testControlBlockIf *inC, outC_testControlBlockIf *outC);

extern void testControlBlockIf_reset(outC_testControlBlockIf *outC);

extern void testControlBlockIf_init(outC_testControlBlockIf *outC);
#endif