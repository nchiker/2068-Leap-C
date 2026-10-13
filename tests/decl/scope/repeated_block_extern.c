// The same extern declaration twice in one block is allowed.
// local: x#1 obj int flags=extern
// sym: x obj int val=0xDFFE
void f(void) { extern int x; extern int x; }
