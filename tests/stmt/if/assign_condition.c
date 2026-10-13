// An assignment's value as the condition; the assignment is done either way.
// expect: exit 0
int main(void)
{
    int a;
    int b;
    if (a = 0) return 1;
    if (!(b = 5)) return 2;
    if (a != 0 || b != 5) return 3;
    return 0;
}
