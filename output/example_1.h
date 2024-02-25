#ifndef _example_1_H_
#define _example_1_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 i;
kcg_bool c;
} inC_example_1;


typedef struct {
kcg_bool init;
kcg_bool init1;
kcg_int32 o;

SSM_ST state_nxt;
} outC_example_1;

extern void example_1(inC_example_1 *inC, outC_example_1 *outC);

extern void example_1_reset(outC_example_1 *outC);

extern void example_1_init(outC_example_1 *outC);
#endif