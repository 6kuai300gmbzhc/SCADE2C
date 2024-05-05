#ifndef _structTest3_H_
#define _structTest3_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_bool in2;
kcg_float32 in3;
} inC_structTest3;


typedef struct {
type3 out1;
type3 out4;
type4 out2;
kcg_bool out3;
} outC_structTest3;

extern void structTest3(inC_structTest3 *inC, outC_structTest3 *outC);

extern void structTest3_reset(outC_structTest3 *outC);

extern void structTest3_init(outC_structTest3 *outC);
#endif