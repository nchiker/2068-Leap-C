// float and double are one type: the Sinclair 5-byte format (Phase 8; spec.md 4.9).
// sym: f obj float size=5
// sym: d obj float size=5
// sym: p obj *float size=2
// sym: a obj [3]float size=15
// sym: g func fn(float,int)float
// sym: s obj struct S size=7
// tag: S struct size=7 members=x@0:float,n@5:int
// data: n 0500
float f;
double d;
float *p;
float a[3];
float g(float x, int k);
struct S { float x; int n; } s;
int n = sizeof(double);
