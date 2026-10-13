// local: T typedef [3]char
// local: v obj [3]char flags=auto
// nosym: T
void f(void) { typedef char T[3]; T v; }
