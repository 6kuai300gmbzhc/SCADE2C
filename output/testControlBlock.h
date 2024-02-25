#ifndef _testControlBlock_H_
#define _testControlBlock_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
kcg_int8 in3;
} inC_testControlBlock;


typedef struct {
kcg_bool init;
kcg_bool init1;
kcg_int8 mem_pre;
kcg_bool init2;
kcg_int8 out1;
kcg_int8 out2;
kcg_int8 out3;
} outC_testControlBlock;

extern void testControlBlock(inC_testControlBlock *inC, outC_testControlBlock *outC);

extern void testControlBlock_reset(outC_testControlBlock *outC);

extern void testControlBlock_init(outC_testControlBlock *outC);
#endif