// sizeof type names (spec.md 4.2).
// sym: a obj [1]char
// sym: b obj [2]char
// sym: c obj [2]char
// sym: d obj [20]char
// sym: e obj [2]char
// sym: f obj [24]char
// sym: g obj [2]char
char a[sizeof(char)];
char b[sizeof(int)];
char c[sizeof(char *)];
char d[sizeof(int [10])];
char e[sizeof(int (*)[10])];
char f[sizeof(char [2][3][4])];
char g[sizeof(void (*)(int))];
