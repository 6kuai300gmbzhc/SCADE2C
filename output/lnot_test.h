_lnot_test_H_
#define _lnot_test_H_
#include "kcg_types.h"

typedef struct {
kcg_uint8 input1;
} inC_lnot_test;


typedef struct {
kcg_uint8 mem_pre;
kcg_bool init;
kcg_uint8 output1;
kcg_uint8 output2;
} outC_lnot_test;

extern void lnot_test(inC_lnot_test *inC, outC_lnot_test *outC);

extern void lnot_test_reset(outC_lnot_test *outC);

extern void lnot_test_init(outC_lnot_test *outC);
