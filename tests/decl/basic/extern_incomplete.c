// An extern array of unknown size has no storage until it is completed.
// sym: a obj [3]int flags= val=0xDFF8
// sym: b obj int val=0xDFFE
extern int a[];
int b;
int a[3];
