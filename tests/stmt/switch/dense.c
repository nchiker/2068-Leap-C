// A dense switch (dense table), with values around zero.
// expect: exit 0
int d(int v)
{
    switch (v) {
    case -2: return 10;
    case -1: return 11;
    case 0: return 12;
    case 1: return 13;
    case 3: return 15;
    case 4: return 16;
    }
    return 99;
}
int main(void)
{
    int i;
    for (i = -2; i <= 4; i++) {
        if (i == 2) { if (d(i) != 99) return 1; continue; }
        if (d(i) != 12 + i) return 2;
    }
    if (d(-3) != 99 || d(5) != 99 || d(32767) != 99 || d(-32768) != 99) return 3;
    return 0;
}
