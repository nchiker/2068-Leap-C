// Brace elision in multi-dimensional arrays (C89 6.5.7).
// data: a 0102 0304 0506
// data: b 0100 0200 0300 0000 0000 0000
// data: c 0102 0300
// sym: d obj [3][2]char
// data: d 0102 0304 0500
char a[3][2] = { 1, 2, 3, 4, 5, 6 };
int b[3][2] = { { 1, 2 }, { 3 } };
char c[2][2] = { 1, 2, { 3 } };
char d[][2] = { 1, 2, 3, 4, 5 };
