// A macro's name inside its own expansion is not expanded again (C89 6.8.3.4), also through
// another macro: A -> B -> A and B -> A -> B end as the identifiers A and B.
// expect: exit 0
int x = 4;
#define x (x + 1)
#define A B
#define B A
int main(void)
{
    int A;
    int B;
    if (x != 5) return 1;
    A = 9;
    B = 3;
    if (A - B != 6) return 2;
    return 0;
}
