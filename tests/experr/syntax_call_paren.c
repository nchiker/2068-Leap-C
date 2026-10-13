// An argument list without its `)`.
// expect: error E_SYNTAX 6
int f(int a, int b) { return a; }
int main(void)
{
    return f(1, 2; /*E*/
}
