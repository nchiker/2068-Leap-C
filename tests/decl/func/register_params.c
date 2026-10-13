// register is accepted on parameters and locals, and ignored.
// sym: f func fn(int,char)void flags=defined
// local: a obj int flags=param
// local: r obj int flags=auto val=0
void f(register int a, register char b) { register int r; }
