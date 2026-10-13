// A function called but never defined: the error is at its first use.
// expect: error E_UNDEFFN 7
int f(int);
int main(void)
{
    int x;
    x = f(1); /*E*/
    return f(2);
}
