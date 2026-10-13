// A static local has static storage and block scope.
// local: count obj int flags=static val=0xDFFE
// local: tab obj [3]char flags=static,defined val=0xDFFB
// nosym: count
void f(void) { static int count; static char tab[3] = { 7, 8, 9 }; }
