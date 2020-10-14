#include <math.h>
#include <stdio.h>

double* MIDWT(double *x, int m, int n, double *h, int lh, int L, double *y);
void bpsconv(double *x_out, int lx, double *g0, double *g1, int lhm1, int lhhm1, double *x_inl, double *x_inh);
