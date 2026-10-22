// A prototype's parameter of function type without a name (an abstract declarator, C89 6.5.4.3): it is
// a pointer to a function (Phase 9: ROM coverage).
// expect: exit 42
int apply(int (int), int);
int twice(int n)
{
    return n * 2;
}
int apply(int f(int), int v)
{
    return f(v);
}
int main(void)
{
    return apply(twice, 21);
}
