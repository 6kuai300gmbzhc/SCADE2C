#ifndef _testStruct_H_
#define _testStruct_H_
#include "kcg_types.h"

typedef struct {
struct1 in1;
} inC_testStruct;


typedef struct {
kcg_float32 out1;
} outC_testStruct;

extern void testStruct(inC_testStruct *inC, outC_testStruct *outC);

extern void testStruct_reset(outC_testStruct *outC);

extern void testStruct_init(outC_testStruct *outC);
#endif