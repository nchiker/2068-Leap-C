// Too many arguments for the prototype.
// expect: error E_ARGS 6
int f(int a, int b) { return a + b; }
int main(void)
{
    return f(1, 2, 3); /*E*/
}
