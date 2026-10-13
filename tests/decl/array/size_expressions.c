// Array sizes are integer constant expressions.
// sym: a obj [12]char
// sym: b obj [7]int
// sym: c obj [2]char
// sym: d obj *[40000]char
// sym: e obj [5]char
char a[3 * 4];
int b[(1 << 3) - 1];
char c[sizeof(int)];
char (*d)[40000u];
char e[10 / 2 % 7];
