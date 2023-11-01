_fby_operator_H_
#define _fby_operator_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 input1;
kcg_int8 input2;
kcg_bool tmp;
} inC_fby_operator;


typedef struct {
kcg_int8 mem_pre;
kcg_int8 mem_pre1;
kcg_bool init;
kcg_int8 output1;
kcg_int8 output2;
} outC_fby_operator;

extern void fby_operator(inC_fby_operator *inC, outC_fby_operator *outC);

extern void fby_operator_reset(outC_fby_operator *outC);

extern void fby_operator_init(outC_fby_operator *outC);
