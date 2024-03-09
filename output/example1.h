#ifndef _example1_H_
#define _example1_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 x;
kcg_int32 y;
} inC_example1;


typedef struct {
kcg_int32 z;
} outC_example1;

extern void example1(inC_example1 *inC, outC_example1 *outC);

extern void example1_reset(outC_example1 *outC);

extern void example1_init(outC_example1 *outC);
#endif
