_bool_expr_H_
#define _bool_expr_H_
#include "kcg_types.h"

typedef struct {
kcg_bool in1;
kcg_bool in2;
kcg_bool in3;
kcg_int8 in4;
kcg_int8 in5;
kcg_int8 in6;
} inC_bool_expr;


typedef struct {
kcg_bool out1;
kcg_bool out2;
kcg_bool out3;
} outC_bool_expr;

extern void bool_expr(inC_bool_expr *inC, outC_bool_expr *outC);

extern void bool_expr_reset(outC_bool_expr *outC);

extern void bool_expr_init(outC_bool_expr *outC);
