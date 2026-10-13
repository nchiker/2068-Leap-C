// break and continue in a while loop, in nested blocks.
// expect: exit 0
int main(void)
{
    int i;
    int s;
    i = 0;
    s = 0;
    while (1) {
        i++;
        if (i > 10) break;
        if (i % 2) { continue; }
        s += i;
    }
    if (i != 11) return 1;
    if (s != 30) return 2;
    return 0;
}
