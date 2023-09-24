_Operator1_H_
#define _Operator1_H_
#include "kcg_types.h"

typedef struct {

} inC_Operator1;


typedef struct {
kcg_int32 Output1;
} outC_Operator1;


extern void Operator1(inC_Operator1 *inC, outC_Operator1 *outC);


extern void Operator1_reset(outC_Operator1 *outC);


extern void Operator1_init(outC_Operator1 *outC);
