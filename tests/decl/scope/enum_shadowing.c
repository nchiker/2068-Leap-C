// local: t obj [5]char
// sym: u obj [1]char
// sym: A enumc int val=1
enum { A = 1 };
void f(void) { enum { A = 5 }; char t[A]; }
char u[A];
