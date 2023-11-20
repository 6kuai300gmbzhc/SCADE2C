_init_operator_H_
#define _init_operator_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 input1;
} inC_init_operator;


typedef struct {
kcg_int8 output1;
kcg_boolinit;
} outC_init_operator;


extern void init_operator(inC_init_operator *inC, outC_init_operator *outC);


extern void init_operator_reset(outC_init_operator *outC);


extern void init_operator_init(outC_init_operator *outC);
