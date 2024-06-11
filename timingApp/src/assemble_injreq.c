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
    vala[4] = *e;  // Future use
    vala[5] = *f;  // Future use
    vala[6] = *g;  // sequence #

    return 0;
}

static long split_injreq(aSubRecord *prec) {
    double *a;
    long *vala, *valb, *valc, *vald, *vale, *valf, *valg;

    //printf("split_injreq\n");

    a = (double *)prec->a;
    vala = (long *)prec->vala;
    valb = (long *)prec->valb;
    valc = (long *)prec->valc;
    vald = (long *)prec->vald;
    vale = (long *)prec->vale;
    valf = (long *)prec->valf;
    valg = (long *)prec->valg;

    //printf("a[0]=%ld a[1]=%ld a[2]=%ld a[3]=%ld a[4]=%ld a[5]=%ld a[6]=%ld\n",
    //        a[0], a[1], a[2], a[3], a[4], a[5], a[6]);

    *vala = a[0];  // Target Bucket
    *valb = a[1];  // # Gun Bunches
    *valc = a[2];  // Injection Mode
    *vald = a[3];  // Gun Inhibit
    *vale = a[4];  // Future use
    *valf = a[5];  // Future use
    *valg = a[6];  // sequence #

    return 0;
}

epicsRegisterFunction(assemble_injreq);
epicsRegisterFunction(split_injreq);
