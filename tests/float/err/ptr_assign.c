// A float does not convert to a pointer (spec.md 4.3).
// expect: error E_TYPE 5
int main(void)
{
    int *p = 1.5;
    return 0;
}
