// (Phase 2: the static data starts below the function's 6-byte function -> line record, spec.md 5.9)
// local: k obj int flags=static,defined val=0xDFF8
// local: m obj [2][2]char flags=static,defined val=0xDFF4
void f(void) { static int k = 5 * 5; static char m[2][2] = { 1, 2, 3 }; }
