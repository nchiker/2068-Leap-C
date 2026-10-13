// Null pointer constants, void pointers both ways, casts (spec.md 4.3).
// data: p0 0000
// data: vp feDF
// data: ip feDF
// data: cp 0050
// data: n feDF
int x;
char *p0 = 0;
void *vp = &x;
int *ip = (void *)&x;
char *cp = (char *)0x5000;
int n = (int)&x;
