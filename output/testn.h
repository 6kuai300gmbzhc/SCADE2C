_testn_H_
#define _testn_H_
#include "kcg_types.h"

typedef struct {
type2 x1;
type2 x2;
} inC_testn;


typedef struct {
type2 y;
} outC_testn;

extern void testn(inC_testn *inC, outC_testn *outC);

extern void testn_reset(outC_testn *outC);

extern void testn_init(outC_testn *outC);
