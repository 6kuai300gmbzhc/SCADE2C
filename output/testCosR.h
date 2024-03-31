#ifndef _testCosR_H_
#define _testCosR_H_
#include "kcg_types.h"

typedef struct {
kcg_float64 x;
} inC_testCosR;


typedef struct {
kcg_float64 y;
} outC_testCosR;

extern void testCosR(inC_testCosR *inC, outC_testCosR *outC);

extern void testCosR_reset(outC_testCosR *outC);

extern void testCosR_init(outC_testCosR *outC);
#endif