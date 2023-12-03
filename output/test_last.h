_test_last_H_
#define _test_last_H_
#include "kcg_types.h"

typedef struct {
kcg_bool tmp;
kcg_int8 in1;
kcg_int8 in2;
} inC_test_last;


typedef struct {
kcg_bool init;
kcg_int32 fbyIdx;
kcg_int8 fbyArray;
kcg_int32 fbyIdx1;
kcg_int8 fbyArray1;
kcg_int8 out1;
kcg_int8 out2;
} outC_test_last;

extern void test_last(inC_test_last *inC, outC_test_last *outC);

extern void test_last_reset(outC_test_last *outC);

extern void test_last_init(outC_test_last *outC);
