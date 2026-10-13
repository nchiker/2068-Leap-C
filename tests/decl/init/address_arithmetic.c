// Address arithmetic in initialisers (not integer constant expressions, but constants).
// data: d 0400
// data: c 0100
// data: e 0600
int arr[10];
int d = &arr[5] - &arr[1];
int c = &arr[1] > &arr[0];
int e = (char *)&arr[3] - (char *)arr;
