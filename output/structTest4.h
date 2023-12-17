_structTest4_H_
#define _structTest4_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in1;
} inC_structTest4;


typedef struct {
tmpStruct out1;
} outC_structTest4;

extern void structTest4(inC_structTest4 *inC, outC_structTest4 *outC);

extern void structTest4_reset(outC_structTest4 *outC);

extern void structTest4_init(outC_structTest4 *outC);
