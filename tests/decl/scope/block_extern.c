// (Phase 2: the static data starts below the function's 6-byte function -> line record, spec.md 5.9)
// extern in a block: the file-scope object, under a block-scope name.
// sym: g obj int val=0xDFF8
// local: g obj int flags=extern val=0xDFF8
// local: h func fn(int)int flags=extern
void f(void) { extern int g; int h(int); }
int g;
