// One specifier list, several declarators of different shapes.
// sym: a obj int
// sym: p obj *int
// sym: v obj [3]int
// sym: f func fn(int)int
// sym: pp obj **int
int a, *p, v[3], f(int), **pp;
