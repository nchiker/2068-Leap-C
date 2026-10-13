// Function pointers and arrays of them (spec.md 4.6).
// sym: fp obj *fn(int,int)int size=2
// sym: tab obj [4]*fn()void size=8
// sym: fpp obj **fn(?)char
// sym: cb obj *fn(*fn(int)void)void
int (*fp)(int, int);
void (*tab[4])(void);
char (**fpp)();
void (*cb)(void (*)(int));
