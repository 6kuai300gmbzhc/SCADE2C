_testChange_H_
#define _testChange_H_
#include "kcg_types.h"

typedef struct {
kcg_float32 in1;
} inC_testChange;


typedef struct {
kcg_float64 out1;
} outC_testChange;

extern void testChange(inC_testChange *inC, outC_testChange *outC);

extern void testChange_reset(outC_testChange *outC);

extern void testChange_init(outC_testChange *outC);
