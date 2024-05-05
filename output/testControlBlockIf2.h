#ifndef _testControlBlockIf2_H_
#define _testControlBlockIf2_H_
#include "kcg_types.h"

typedef struct {
kcg_float32 in1;
kcg_float32 in2;
kcg_float32 in5;
kcg_int32 in3;
kcg_int32 in4;
enum_case in6;
} inC_testControlBlockIf2;


typedef struct {
kcg_int32 mem_pre;
kcg_bool init;
kcg_int32 mem_pre1;
kcg_bool init1;
kcg_bool init2;
kcg_int32 mem_pre2;
kcg_bool init3;
kcg_int32 out2;
kcg_int32 out3;
kcg_int32 fbyIdx;
kcg_int32 fbyArray[5];
} outC_testControlBlockIf2;

extern void testControlBlockIf2(inC_testControlBlockIf2 *inC, outC_testControlBlockIf2 *outC);

extern void testControlBlockIf2_reset(outC_testControlBlockIf2 *outC);

extern void testControlBlockIf2_init(outC_testControlBlockIf2 *outC);
#endif