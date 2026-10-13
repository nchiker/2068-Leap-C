// Array and function parameters become pointers (C89 6.7.1).
// sym: f func fn(*int,*[4]char,*fn(int)int)void
void f(int a[], char m[3][4], int g(int));
