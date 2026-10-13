// A value returned from a void function.
// expect: error E_TYPE 5
void f(void)
{
    return 1; /*E*/
}
int main(void) { f(); return 0; }
