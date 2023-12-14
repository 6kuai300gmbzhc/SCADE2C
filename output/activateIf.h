_activateIf_H_
#define _activateIf_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 in1;
kcg_int32 in2;
} inC_activateIf;


typedef struct {
kcg_bool init;
<<<<<<< HEAD
kcg_int32 out;
kcg_int32 fbyIdx;
kcg_int32 fbyArray[5];
=======
kcg_int32 fbyIdx;
kcg_int32 fbyArray;
kcg_int32 out;
>>>>>>> 0d8cdef58357f3477d64df68272653292ca0792d
} outC_activateIf;

extern void activateIf(inC_activateIf *inC, outC_activateIf *outC);

extern void activateIf_reset(outC_activateIf *outC);

extern void activateIf_init(outC_activateIf *outC);
