_strong_automaton_H_
#define _strong_automaton_H_
#include "kcg_types.h"

typedef struct {
kcg_int32 i;
kcg_bool c;
kcg_bool d;
} inC_strong_automaton;


typedef struct {
kcg_bool init;
kcg_bool init1;
kcg_int32 o;

SSM_ST state_nxt;
} outC_strong_automaton;

extern void strong_automaton(inC_strong_automaton *inC, outC_strong_automaton *outC);

extern void strong_automaton_reset(outC_strong_automaton *outC);

extern void strong_automaton_init(outC_strong_automaton *outC);
