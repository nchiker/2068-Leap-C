// A struct argument to an unprototyped function (struct parameters are not supported).
// expect: error E_OPERAND 8
struct s { int a; };
struct s v;
int f();
int main(void)
{
    return f(v); /*E*/
}
int f(int a) { return a; }
