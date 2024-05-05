#ifndef _testControlBlockWhen_H_
#define _testControlBlockWhen_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in3;
kcg_int32 in4;
kcg_int32 in7;
enum_case in5;
enum_case in6;
} inC_testControlBlockWhen;


typedef struct {
kcg_bool init;
kcg_int32 mem_pre;
kcg_bool init1;
kcg_int32 out1;
kcg_int32 out2;
kcg_int32 out3;
kcg_int32 fbyIdx;
kcg_int32 fbyArray[4];
} outC_testControlBlockWhen;

extern void testControlBlockWhen(inC_testControlBlockWhen *inC, outC_testControlBlockWhen *outC);

extern void testControlBlockWhen_reset(outC_testControlBlockWhen *outC);

extern void testControlBlockWhen_init(outC_testControlBlockWhen *outC);
#endif