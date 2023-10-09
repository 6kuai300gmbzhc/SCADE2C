_pre_example_H_
#define _pre_example_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 input1;
kcg_int32 input2;
} inC_pre_example;


typedef struct {
kcg_int32 output1;
kcg_int32 output2;
} outC_pre_example;

extern void pre_example(inC_pre_example *inC, outC_pre_example *outC);

extern void pre_example_reset(outC_pre_example *outC);

extern void pre_example_init(outC_pre_example *outC);
