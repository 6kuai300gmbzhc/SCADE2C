_pre_if3_H_
#define _pre_if3_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 input1;
kcg_int8 input2;
kcg_bool tmp;
} inC_pre_if3;


typedef struct {
kcg_bool init;
kcg_int8 output1;
kcg_int8 output2;
} outC_pre_if3;

extern void pre_if3(inC_pre_if3 *inC, outC_pre_if3 *outC);

extern void pre_if3_reset(outC_pre_if3 *outC);

extern void pre_if3_init(outC_pre_if3 *outC);
