#ifndef _Square_H_
#define _Square_H_
#include "kcg_types.h"

typedef struct {
kcg_float64 Square_In;
} inC_Square;


typedef struct {
kcg_float64 Square_Out;
} outC_Square;

extern void Square(inC_Square *inC, outC_Square *outC);

extern void Square_reset(outC_Square *outC);

extern void Square_init(outC_Square *outC);
#endif