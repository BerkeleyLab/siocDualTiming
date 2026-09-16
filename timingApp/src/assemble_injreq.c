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
    vala[4] = *e;  // AR target Bucket
    vala[5] = *f;  // Future use
    vala[6] = *g;  // sequence #

    return 0;
}

static long split_injreq(aSubRecord *prec) {
    double *a;
    double injModeVal;
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

    // Convert injection mode RVAL to VAL
    //record(mbbo, "$(T)TimInjMode") {
    //    field(DESC, "Injection Mode")
    //    field(OMSL, "supervisory")
    //    field(ZRST, "Default")
    //    field(ONST, "Linac Tuning")
    //    field(TWST, "BR Tuning")
    //    field(THST, "BTS Tuning")
    //    field(FRST, "SR Inj Prep")
    //    field(FVST, "SR Injection")
    //    field(SXST, "SR Tuning")
    //    field(SVST, "Topoff Intlk Test")
    //    field(EIST, "AR Injection")
    //    field(ZRVL, "0")
    //    field(ONVL, "10")
    //    field(TWVL, "20")
    //    field(THVL, "30")
    //    field(FRVL, "41")
    //    field(FVVL, "40")
    //    field(SXVL, "42")
    //    field(SVVL, "50")
    //    field(EIVL, "60")
    //    info(archive,"Slow")
    //}
    switch((int)a[2]) {
        case 0:  injModeVal = 0; break;
        case 10: injModeVal = 1; break;
        case 20: injModeVal = 2; break;
        case 30: injModeVal = 3; break;
        // Mode 4 (SR injection prep) is 41
        case 41: injModeVal = 4; break;
        // Mode 5 (SR injection) is 40
        case 40: injModeVal = 5; break;
        case 42: injModeVal = 6; break;
        case 50: injModeVal = 7; break;
        case 60: injModeVal = 8; break;
        default: injModeVal = 0; break;
    }

    *vala = a[0];       // Target Bucket
    *valb = a[1];       // # Gun Bunches
    *valc = injModeVal; // Injection Mode
    *vald = a[3];       // Gun Inhibit
    *vale = a[4];       // AR Target Bucket
    *valf = a[5];       // Future use
    *valg = a[6];       // sequence #

    return 0;
}

epicsRegisterFunction(assemble_injreq);
epicsRegisterFunction(split_injreq);
