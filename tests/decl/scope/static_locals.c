// (Phase 2: the static data starts below the function's 6-byte function -> line record, spec.md 5.9)
// A static local has static storage and block scope.
// local: count obj int flags=static val=0xDFF8
// local: tab obj [3]char flags=static,defined val=0xDFF5
// nosym: count
void f(void) { static int count; static char tab[3] = { 7, 8, 9 }; }
