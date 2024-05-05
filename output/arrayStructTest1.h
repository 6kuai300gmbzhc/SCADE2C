#ifndef _arrayStructTest1_H_
#define _arrayStructTest1_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
kcg_bool in3;
typename1 in4;
typename1 in5;
} inC_arrayStructTest1;


typedef struct {
typename1 o1[3];
typename1 o2[3];
kcg_int8 o3;
} outC_arrayStructTest1;

extern void arrayStructTest1(inC_arrayStructTest1 *inC, outC_arrayStructTest1 *outC);

extern void arrayStructTest1_reset(outC_arrayStructTest1 *outC);

extern void arrayStructTest1_init(outC_arrayStructTest1 *outC);
#endif