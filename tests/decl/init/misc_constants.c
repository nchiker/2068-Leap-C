// data: a 0600
// data: b 6200
// data: c 00ff
// data: e 0200
// data: z 0000
// data: q 005c
int a = sizeof(struct { int x; char y[4]; });
int b = 'a' + 1;
char c[2] = { 256, -1 };
enum col { R, G, B } e = B;
char *z = 0;
int *q = (int *)0x5C00;
