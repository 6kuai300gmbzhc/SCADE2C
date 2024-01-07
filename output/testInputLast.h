#ifndef _testInputLast_H_
#define _testInputLast_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
} inC_testInputLast;


typedef struct {
kcg_int8 in1;
kcg_int8 out1;
} outC_testInputLast;

extern void testInputLast(inC_testInputLast *inC, outC_testInputLast *outC);

extern void testInputLast_reset(outC_testInputLast *outC);

extern void testInputLast_init(outC_testInputLast *outC);
#endif