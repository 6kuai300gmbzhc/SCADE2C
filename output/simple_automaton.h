_simple_automaton_H_
#define _simple_automaton_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 i;
kcg_bool c;
kcg_bool d;
} inC_simple_automaton;


typedef struct {
kcg_bool init;
kcg_int32 o;

SSM_ST state_nxt;
} outC_simple_automaton;

extern void simple_automaton(inC_simple_automaton *inC, outC_simple_automaton *outC);

extern void simple_automaton_reset(outC_simple_automaton *outC);

extern void simple_automaton_init(outC_simple_automaton *outC);
