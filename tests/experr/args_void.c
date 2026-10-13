// Arguments to a (void) prototype.
// expect: error E_ARGS 7
int f(void) { return 1; }
int main(void)
{
    return f(
        1); /*E*/
}
