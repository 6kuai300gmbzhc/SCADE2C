_pre_if2_H_
#define _pre_if2_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 input1;
kcg_int8 input2;
kcg_bool tmp;
} inC_pre_if2;


typedef struct {
kcg_int8 mem_pre;
kcg_int8 mem_pre1;
kcg_bool init;
kcg_int8 output1;
kcg_int8 output2;
} outC_pre_if2;

extern void pre_if2(inC_pre_if2 *inC, outC_pre_if2 *outC);

extern void pre_if2_reset(outC_pre_if2 *outC);

extern void pre_if2_init(outC_pre_if2 *outC);
