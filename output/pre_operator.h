_pre_operator_H_
#define _pre_operator_H_
#include "kcg_types.h"

typedef struct {
kcg_float64 input1;
kcg_float64 input2;
} inC_pre_operator;


typedef struct {
kcg_bool init;
kcg_float64 output1;
kcg_float64 output2;
} outC_pre_operator;

extern void pre_operator(inC_pre_operator *inC, outC_pre_operator *outC);

extern void pre_operator_reset(outC_pre_operator *outC);

extern void pre_operator_init(outC_pre_operator *outC);
