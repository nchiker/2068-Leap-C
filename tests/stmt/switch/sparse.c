// A sparse switch (sparse table), every case, the default and fall-through.
// expect: exit 0
int s(int v)
{
    int r;
    r = 0;
    switch (v) {
    case 1000: r = 1; break;
    case -7: r = 2; break;
    case 3: r = 3;
    case 400: r += 4; break;
    default: r = 9;
    }
    return r;
}
int main(void)
{
    if (s(1000) != 1) return 1;
    if (s(-7) != 2) return 2;
    if (s(3) != 7) return 3;
    if (s(400) != 4) return 4;
    if (s(0) != 9) return 5;
    if (s(-32768) != 9) return 6;
    return 0;
}
