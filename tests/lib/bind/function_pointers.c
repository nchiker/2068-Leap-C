// Library functions have addresses: function pointers of their exact types, a table of them,
// calls through the pointers.
// expect: exit 0
unsigned (*len)(void *) = strlen;
int (*cmp)(void *, void *);
int (*ops[2])(int);
int main(void)
{
    cmp = strcmp;
    ops[0] = abs;
    ops[1] = putchar;
    if (len("four") != 4) return 1;
    if (cmp("a", "b") >= 0) return 2;
    if (ops[0](-9) != 9) return 3;
    if (len != strlen || ops[1] != putchar) return 4;
    return 0;
}
