// (Phase 2: the static data starts below the function's 6-byte function -> line record, spec.md 5.9)
// The same extern declaration twice in one block is allowed.
// local: x#1 obj int flags=extern
// sym: x obj int val=0xDFF8
void f(void) { extern int x; extern int x; }
