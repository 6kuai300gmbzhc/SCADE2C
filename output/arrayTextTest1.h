#ifndef _arrayTextTest1_H_
#define _arrayTextTest1_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
kcg_int8 in3;
} inC_arrayTextTest1;


typedef struct {
kcg_int8 o1[3];
kcg_int8 o3;
} outC_arrayTextTest1;

extern void arrayTextTest1(inC_arrayTextTest1 *inC, outC_arrayTextTest1 *outC);

extern void arrayTextTest1_reset(outC_arrayTextTest1 *outC);

extern void arrayTextTest1_init(outC_arrayTextTest1 *outC);
#endif