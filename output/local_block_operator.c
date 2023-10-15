#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "local_block_operator.h"
void local_block_operator(inC_local_block_operator *inC, outC_local_block_operator *outC)
{
kcg_bool tmp1;
kcg_int8 tmp2;
tmp1=inC->input2;
tmp2=inC->input1+kcg_lit_int8(1);
outC->output2=tmp1;
outC->output1=inC->input1+tmp2+kcg_lit_int8(2);

}
void local_block_operator_init(outC_local_block_operator *outC)
{
outC->output1=kcg_lit_int8(0);
outC->output2=kcg_true;
}
void local_block_operator_reset(outC_local_block_operator *outC)
{
}
