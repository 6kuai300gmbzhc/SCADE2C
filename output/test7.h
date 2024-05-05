_test7_H_
#define _test7_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
} inC_test7;


typedef struct {
kcg_int8 out1;
} outC_test7;

extern void test7(inC_test7 *inC, outC_test7 *outC);

extern void test7_reset(outC_test7 *outC);

extern void test7_init(outC_test7 *outC);
