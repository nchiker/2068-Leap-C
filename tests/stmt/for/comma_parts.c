// Comma expressions in the parts; a downward loop with an unsigned counter.
// expect: exit 0
int main(void)
{
    int i;
    int j;
    unsigned u;
    int n;
    n = 0;
    for (i = 0, j = 10; i < j; i++, j--) n++;
    if (n != 5) return 1;
    n = 0;
    for (u = 3; u != 65535; u--) n++;
    if (n != 4) return 2;
    return 0;
}
