// Partial lists are zero-filled; [] takes its size from the list.
// sym: a obj [4]int
// data: a 01000200030004 00
// sym: b obj [5]char
// data: b 0102000000
// sym: c obj [3]int
// data: c 0a00140000 00
// sym: d obj [2]char
// data: d 0000
int a[4] = { 1, 2, 3, 4 };
char b[5] = { 1, 2 };
int c[] = { 10, 20, 0 };
char d[2] = { };
