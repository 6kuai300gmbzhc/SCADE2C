#ifndef _testManyList_H_
#define _testManyList_H_
#include "kcg_types.h"

typedef struct {
struct1 in1;
} inC_testManyList;


typedef struct {
kcg_int8 out1;
kcg_float32 out2;
} outC_testManyList;

extern void testManyList(inC_testManyList *inC, outC_testManyList *outC);

extern void testManyList_reset(outC_testManyList *outC);

extern void testManyList_init(outC_testManyList *outC);
#endif