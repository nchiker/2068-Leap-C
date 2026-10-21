// Address constants: a multi-dimensional element, a string literal plus an offset, void *.
// sym: arr obj [2][3]int val=0xDFF2
// data: pe f6df
// data: ps ebdf
// data: pv fedf
int x;
int arr[2][3];
int *pe = &arr[0][2];
char *ps = "abc" + 1;
void *pv = &x;
