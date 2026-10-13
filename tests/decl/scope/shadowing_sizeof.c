// Inner declarations hide outer ones; sizeof sees the innermost (the ROM's own lookup).
// local: a1 obj [1]char
// local: a2 obj [2]char
// local: a3 obj [10]char
// sym: g obj [2]char
int x;
void f(void) {
  char x;
  char a1[sizeof x];
  {
    int *x;
    char a2[sizeof x];
    { char x[10]; char a3[sizeof x]; }
  }
}
char g[sizeof x];
