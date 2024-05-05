#ifndef _arrayTextTest9_H_
#define _arrayTextTest9_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
kcg_bool in3;
kcg_bool in4;
struct5 in5;
struct5 in6;
} inC_arrayTextTest9;


typedef struct {
struct5 o1[2][3];
kcg_int8 o2;
} outC_arrayTextTest9;

extern void arrayTextTest9(inC_arrayTextTest9 *inC, outC_arrayTextTest9 *outC);

extern void arrayTextTest9_reset(outC_arrayTextTest9 *outC);

extern void arrayTextTest9_init(outC_arrayTextTest9 *outC);
#endif