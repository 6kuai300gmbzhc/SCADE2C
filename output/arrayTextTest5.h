#ifndef _arrayTextTest5_H_
#define _arrayTextTest5_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1[2][3][4];
} inC_arrayTextTest5;


typedef struct {
kcg_int8 o1[2][3][4];
} outC_arrayTextTest5;

extern void arrayTextTest5(inC_arrayTextTest5 *inC, outC_arrayTextTest5 *outC);

extern void arrayTextTest5_reset(outC_arrayTextTest5 *outC);

extern void arrayTextTest5_init(outC_arrayTextTest5 *outC);
#endif