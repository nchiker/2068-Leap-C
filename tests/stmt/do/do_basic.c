// do/while runs its body at least once.
// expect: exit 0
int main(void)
{
    int i;
    int n;
    i = 0;
    n = 0;
    do n++; while (0);
    if (n != 1) return 1;
    do { i += 3; n++; } while (i < 10);
    if (i != 12 || n != 5) return 2;
    return 0;
}
