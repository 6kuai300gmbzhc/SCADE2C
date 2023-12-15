_structTest_H_
#define _structTest_H_
#include "kcg_types.h"

typedef struct {
tmpStruct in1;
} inC_structTest;


typedef struct {
kcg_int32 o1;
} outC_structTest;

extern void structTest(inC_structTest *inC, outC_structTest *outC);

extern void structTest_reset(outC_structTest *outC);

extern void structTest_init(outC_structTest *outC);
