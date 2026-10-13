// for with each part left out.
// expect: exit 0
int main(void)
{
    int i;
    int n;
    i = 0;
    for (; i < 5; i++) ;
    if (i != 5) return 1;
    for (i = 0; i < 5;) i += 2;
    if (i != 6) return 2;
    n = 0;
    for (i = 0;; i++) { if (i == 4) break; n++; }
    if (n != 4) return 3;
    n = 0;
    for (;;) { if (++n == 9) break; }
    if (n != 9) return 4;
    return 0;
}
