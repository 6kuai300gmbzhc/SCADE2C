#include "kcg_consts.h"
#include "kcg_sensors.h"
#include "fby_operator.h"
void fby_operator(inC_fby_operator *inC, outC_fby_operator *outC)
{
if(outC->init){
 outC->init=false;
for(int tmp=0;tmp<kcg_lit_int32(6);tmp++){
        outC->fbyArray[tmp]=inC->input2+kcg_lit_int8(2);
}
        outC->fbyIdx=0;
outC->output2=kcg_lit_int8(1);
}
else{
outC->output2=outC->fbyArray[outC->fbyIdx];
}
outC->output1=outC->output2+kcg_lit_int8(2);
outC->fbyArray[outC->fbyIdx]=inC->input1+kcg_lit_int8(2);
outC->fbyIdx=(outC->fbyIdx+1)%(kcg_lit_int32(6));

}
void fby_operator_init(outC_fby_operator *outC)
{
outC->init=kcg_true;
outC->fbyIdx=kcg_lit_int32(0);
outC->output1=kcg_lit_int8(0);
outC->output2=kcg_lit_int8(0);
for(int idx=0;idx<kcg_lit_int32(6);idx++){
outC->fbyArray[idx]=kcg_lit_int8(0);
}
}
void fby_operator_reset(outC_fby_operator *outC)
{
}
