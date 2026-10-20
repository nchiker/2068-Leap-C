// #pragma hires (spec.md 3.2): with image region 4 reserved, mode(1) is allowed even though
// regions 1-3 are full of data; the code goes to the room left in region 1.
// expect: exit 0
// region: a 1
// region: b 2
// region: c 3
// region: main 1
// cell: GFX_MODE 0
#pragma hires
char a[7900];
char b[4480];
char c[1024];
int main(void)
{
    mode(1);
    plot(10, 10);
    a[0] = 1;
    b[0] = 2;
    c[0] = 3;
    return point(10, 10) + a[0] + b[0] + c[0] - 7;
}
