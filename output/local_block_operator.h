_local_block_operator_H_
#define _local_block_operator_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 input1;
kcg_bool input2;
} inC_local_block_operator;


typedef struct {
kcg_int8 output1;
kcg_bool output2;
} outC_local_block_operator;

extern void local_block_operator(inC_local_block_operator *inC, outC_local_block_operator *outC);

extern void local_block_operator_reset(outC_local_block_operator *outC);

extern void local_block_operator_init(outC_local_block_operator *outC);
