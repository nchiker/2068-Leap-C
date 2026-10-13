// A pointer returned from an int function.
// expect: error E_TYPE 6
int x;
int f(void)
{
    return &x; /*E*/
}
int main(void) { return f(); }
