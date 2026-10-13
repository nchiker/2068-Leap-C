// Address constants: &object, arrays, members and element addresses (static storage).
// sym: x obj int val=0xDFFE
// sym: arr obj [4]int val=0xDFF6
// data: px feDF
// data: pa f6DF
// data: pe faDF
// data: pend feDF
// sym: s obj struct{a:int,b:[3]char} val=0xDFE9
// data: pb ebDF
// data: pc edDF
int x;
int arr[4];
int *px = &x;
int *pa = arr;
int *pe = &arr[2];
int *pend = arr + 4;
struct { int a; char b[3]; } s;
char *pb = s.b;
char *pc = &s.b[2];
