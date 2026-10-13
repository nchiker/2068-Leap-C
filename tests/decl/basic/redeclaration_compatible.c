// Repeated compatible file-scope declarations share one entry and one storage.
// sym: x obj int flags=defined val=0xDFFE
// sym: f func fn(int)int
// sym: a obj [4]int size=8
// data: x 0700
extern int x;
int x;
int x = 7;
extern int x;
int f(int);
int f(int);
extern int a[];
int a[4];
