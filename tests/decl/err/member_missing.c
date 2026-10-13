// expect: error E_MEMBER 3
struct s { int a; } v;
char a[sizeof v.b];
