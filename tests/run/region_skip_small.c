// Region 1 is full and region 2 has 5 bytes left (less than an instruction unit and its link):
// the code goes to region 3.
// expect: exit 3
// region: main 3
char a[8192];
char b[4475];
int main(void) { a[0] = 1; b[0] = 2; return a[0] + b[0]; }
