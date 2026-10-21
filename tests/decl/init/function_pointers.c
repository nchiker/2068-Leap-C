// Function addresses in static initialisers, the functions defined later (their fixups).
// sym: p obj *fn()int
// sym: tab obj [2]*fn(?)int
// sym: o obj struct ops
int f(void);
int g(void);
int (*p)(void) = f;
int (*tab[])() = { f, g };
struct ops { int (*h)(void); int n; } o = { g, 3 };
int f(void) { return 1; }
int g(void) { return 2; }
