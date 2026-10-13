// Redundant parentheses around names and declarators.
// sym: a obj int
// sym: b obj *char
// sym: c obj [2]int
// sym: f func fn(int)int
int (a);
char (*(b));
int ((c))[2];
int (f)(int);
