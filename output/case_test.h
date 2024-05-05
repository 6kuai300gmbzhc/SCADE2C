#ifndef _case_test_H_
#define _case_test_H_
#include "kcg_types.h"

typedef struct {
kcg_bool in1;
kcg_bool in2;
kcg_bool in3;
enum_case in4;
} inC_case_test;


typedef struct {
kcg_bool out1;
} outC_case_test;

extern void case_test(inC_case_test *inC, outC_case_test *outC);

extern void case_test_reset(outC_case_test *outC);

extern void case_test_init(outC_case_test *outC);
#endif