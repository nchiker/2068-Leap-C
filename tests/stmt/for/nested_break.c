// Nested loops: break and continue act on the innermost loop.
// expect: exit 0
int main(void)
{
    int i;
    int j;
    int n;
    n = 0;
    for (i = 0; i < 5; i++) {
        for (j = 0; j < 10; j++) {
            if (j == i) break;
            if (j == 1) continue;
            n++;
        }
        if (i == 3) continue;
        n += 100;
    }
    if (n != 4 * 100 + 0 + 1 + 1 + 2 + 3) return 1;
    return 0;
}
