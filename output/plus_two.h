_plus_two_H_
#define _plus_two_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 x;
} inC_plus_two;


typedef struct {
kcg_int8 y;
} outC_plus_two;


extern void plus_two(inC_plus_two *inC, outC_plus_two *outC);


extern void plus_two_reset(outC_plus_two *outC);


extern void plus_two_init(outC_plus_two *outC);
