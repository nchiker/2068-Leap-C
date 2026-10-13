// ! of a struct.
// expect: error E_OPERAND 7
struct s { int a; };
struct s v;
int main(void)
{
    return !v; /*E*/
}
