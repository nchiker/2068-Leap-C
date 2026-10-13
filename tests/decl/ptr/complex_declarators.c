// Classic hard declarators, read inside out.
// sym: f func fn(int)*fn(char)int
// sym: g obj [3]*fn()*[5]char
// sym: h func fn(*fn(int)void)*fn(int)void
int (*f(int))(char);
char (*(*g[3])(void))[5];
void (*h(void (*)(int)))(int);
