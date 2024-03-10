#ifndef _arrayTextTest10_H_
#define _arrayTextTest10_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
} inC_arrayTextTest10;


typedef struct {
struct6 o1;
} outC_arrayTextTest10;

extern void arrayTextTest10(inC_arrayTextTest10 *inC, outC_arrayTextTest10 *outC);

extern void arrayTextTest10_reset(outC_arrayTextTest10 *outC);

extern void arrayTextTest10_init(outC_arrayTextTest10 *outC);
#endif