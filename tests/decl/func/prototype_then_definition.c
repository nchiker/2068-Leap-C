// The definition after a prototype; an unprototyped declaration completed by a prototype.
// sym: f func fn(int)int flags=defined
// sym: g func fn(*char)void
int f(int);
int f(int x) { }
void g();
void g(char *);
