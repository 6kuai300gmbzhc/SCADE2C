_nat_H_
#define _nat_H_
#include "kcg_types.h"

typedef struct {
kcg_uint64 in;
} inC_nat;


typedef struct {
kcg_uint64 mem_pre;
kcg_bool init;
kcg_uint64 n;
} outC_nat;

extern void nat(inC_nat *inC, outC_nat *outC);

extern void nat_reset(outC_nat *outC);

extern void nat_init(outC_nat *outC);
