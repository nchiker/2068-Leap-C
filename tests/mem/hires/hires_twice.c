// #pragma hires may appear more than once and anywhere a directive may (here inside a function);
// a program that fits regions 1-3 is unchanged by it.
// expect: exit 42
// region: f 1
#pragma hires
int f(int x)
{
#pragma hires
    return x * 2;
}
int main(void)
{
    mode(1);
    mode(0);
    return f(21);
}
