// data: a 0300 0800 1400
enum { R = 3 };
struct big { char x[20]; };
int a[3] = { R, sizeof(int *) * 4, sizeof(struct big) };
