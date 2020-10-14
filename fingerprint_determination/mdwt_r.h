#include <math.h>
#include <stdio.h>

double* mDWT(double *x, int m, int n, double *h, int lh, int L, double *y);
void fpsconv(double *x_in, int lx, double *h0, double *h1, int lhm1, double *x_outl, double *x_outh);
