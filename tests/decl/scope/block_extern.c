// extern in a block: the file-scope object, under a block-scope name.
// sym: g obj int val=0xDFFE
// local: g obj int flags=extern val=0xDFFE
// local: h func fn(int)int flags=extern
void f(void) { extern int g; int h(int); }
int g;
