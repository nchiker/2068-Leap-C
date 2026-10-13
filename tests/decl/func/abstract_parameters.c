// Unnamed parameters with abstract declarators.
// sym: f func fn(*int,*[3]int,**char,*fn(char)int)int
int f(int *, int (*)[3], char **, int (*)(char));
