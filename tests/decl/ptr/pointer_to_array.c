// Parenthesised declarators: pointer to array vs array of pointers.
// sym: pa obj *[10]int size=2
// sym: ap obj [10]*int size=20
// sym: ppa obj **[3][4]char
// sym: pinc obj *[]int
int (*pa)[10];
int *ap[10];
char (**ppa)[3][4];
int (*pinc)[];
