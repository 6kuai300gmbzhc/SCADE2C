_order_list_H_
#define _order_list_H_
#include "kcg_types.h"

typedef struct {
kcg_int8 in1;
kcg_int8 in2;
} inC_order_list;


typedef struct {
kcg_int8 out1;
} outC_order_list;

extern void order_list(inC_order_list *inC, outC_order_list *outC);

extern void order_list_reset(outC_order_list *outC);

extern void order_list_init(outC_order_list *outC);
