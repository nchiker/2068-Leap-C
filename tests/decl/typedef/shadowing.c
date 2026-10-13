// An object in a block hides a typedef name; the typedef is visible again afterwards.
// sym: T typedef char
// local: T obj int flags=auto
// local: arr obj [2]char flags=auto
// sym: after obj [1]char
typedef char T;
void f(void) { int T; { char arr[sizeof T]; } }
char after[sizeof(T)];
