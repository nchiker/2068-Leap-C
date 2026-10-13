// A block's initialiser runs each time the block is entered.
// expect: exit 0
int main(void)
{
    int i;
    int s;
    s = 0;
    for (i = 0; i < 4; i++) {
        int k = 10;
        k += i;
        s += k;
    }
    if (s != 46) return 1;
    return 0;
}
