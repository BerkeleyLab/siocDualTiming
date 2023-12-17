#include <stdio.h>
#include "aSubRecord.h"
#include <registryFunction.h>
#include <epicsExport.h>

static long assemble_injreq(aSubRecord *prec) {
    long *a, *b, *c, *d, *e, *f, *g;
    double *vala;

    //printf("assemble_injreq\n");

    a = (long *)prec->a;
    b = (long *)prec->b;
    c = (long *)prec->c;
    d = (long *)prec->d;
    e = (long *)prec->e;
    f = (long *)prec->f;
    g = (long *)prec->g;
    vala = (double *)prec->vala;

    //printf("a=%ld b=%ld c=%ld d=%ld e=%ld f=%ld g=%ld\n",
    //        *a, *b, *c, *d, *e, *f, *g);

    vala[0] = *a;  // Target Bucket
    vala[1] = *b;  // # Gun Bunches
    vala[2] = *c;  // Injection Mode
    vala[3] = *d;  // Gun Inhibit
    vala[4] = *e;  // Injection field sync delay
    vala[5] = *f;  // Extraction field sync delay
    vala[6] = *g;  // sequence #

    return 0;
}

epicsRegisterFunction(assemble_injreq);
