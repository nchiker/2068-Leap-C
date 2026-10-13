// A loop whose condition is false at once; while (0).
// expect: exit 7
int main(void)
{
    int x;
    x = 7;
    while (x < 0) x = 1;
    while (0) x = 2;
    return x;
}
