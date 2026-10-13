// sym: f func fn()*char
// sym: g func fn(int)**struct s
// sym: h func fn()*[4]int
char *f(void);
struct s;
struct s **g(int);
int (*h(void))[4];
