_case_test_H_
#define _case_test_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
kcg_int8 in3;
kcg_char in4;
} inC_case_test;


typedef struct {
kcg_int8 out1;
kcg_int8 out2;
} outC_case_test;

extern void case_test(inC_case_test *inC, outC_case_test *outC);

extern void case_test_reset(outC_case_test *outC);

extern void case_test_init(outC_case_test *outC);
