// sizeof an expression uses its type, without evaluating it; arrays are not converted.
// sym: a obj [20]char
// sym: b obj [2]char
// sym: c obj [10]char
// sym: d obj [2]char
// sym: e obj [2]char
// sym: f obj [4]char
// sym: g obj [1]char
// sym: h obj [2]char
// sym: n obj [10]char
int t[10];
char *s;
char a[sizeof t];
char b[sizeof t[3]];
char c[sizeof t / sizeof t[0]];
char d[sizeof &t];
char e[sizeof (t + 1)];
char f[sizeof "abc"];
char g[sizeof *s];
char h[sizeof 'x'];
char n[sizeof(t) / sizeof(t[0])];
