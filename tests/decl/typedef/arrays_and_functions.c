// Typedefs of array, pointer and function types.
// sym: Vec typedef [3]int
// sym: Fn typedef fn(int)int
// sym: Str typedef *char
// sym: m obj [2][3]int size=12
// sym: pf obj *fn(int)int
// sym: f func fn(int)int
// sym: names obj [4]*char
typedef int Vec[3];
typedef int Fn(int);
typedef char *Str;
Vec m[2];
Fn *pf;
Fn f;
Str names[4];
