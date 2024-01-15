#ifndef _testfby_H_
#define _testfby_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
} inC_testfby;


typedef struct {
kcg_bool init;
kcg_int8 out1;
kcg_int8 out2;
kcg_int32 fbyIdx;
kcg_int8 fbyArray[4];
} outC_testfby;

extern void testfby(inC_testfby *inC, outC_testfby *outC);

extern void testfby_reset(outC_testfby *outC);

extern void testfby_init(outC_testfby *outC);
#endif