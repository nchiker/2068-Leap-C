// An argument is checked against its prototype parameter.
// expect: error E_TYPE 7
int f(int *p) { return *p; }
char c;
int main(void)
{
    return f(&c); /*E*/
}
