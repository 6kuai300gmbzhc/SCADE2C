_testPara_H_
#define _testPara_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in1[2];
kcg_float32 in2;
} inC_testPara;


typedef struct {
kcg_float32 mem_last;
kcg_float32 mem_last1;
kcg_int32 out1;
kcg_float32 out2;
kcg_float32 out3;
kcg_float32 out4;
} outC_testPara;

extern void testPara(inC_testPara *inC, outC_testPara *outC);

extern void testPara_reset(outC_testPara *outC);

extern void testPara_init(outC_testPara *outC);
