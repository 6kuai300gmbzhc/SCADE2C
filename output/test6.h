_test6_H_
#define _test6_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_bool in2;
type12 in3;
} inC_test6;


typedef struct {
type11 out1;
type11 out2;
type12 out3;
} outC_test6;

extern void test6(inC_test6 *inC, outC_test6 *outC);

extern void test6_reset(outC_test6 *outC);

extern void test6_init(outC_test6 *outC);
