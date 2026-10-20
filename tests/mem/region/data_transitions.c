// Static data in every region, first fit top down (spec.md 3.2): b, c and d fill regions 2, 3 and
// 4 up to the byte (d leaves 144 bytes); e then goes back to the room left in region 1, and f,
// larger than what is left there, to the room left in region 4. The code (main) is in region 1, below the data.
// expect: exit 21
// region: a 1
// region: b 2
// region: c 3
// region: d 4
// region: e 1
// region: f 4
// region: main 1
char a[7950];
char b[4480];
char c[1024];
char d[6000];
char e[100];
char f[143];
int main(void)
{
    a[0] = 1;
    b[4479] = 2;
    c[0] = 3;
    d[5999] = 4;
    e[0] = 5;
    f[142] = 6;
    return a[0] + b[4479] + c[0] + d[5999] + e[0] + f[142];
}
