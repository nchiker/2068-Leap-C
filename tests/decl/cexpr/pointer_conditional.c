// ?: with a pointer and a null pointer constant has the pointer's type.
// data: p feDF
// data: q 0000
// sym: s obj [2]char
int x;
int *p = 1 ? &x : 0;
int *q = 0 ? &x : 0;
char s[sizeof(1 ? 0 : &x)];
