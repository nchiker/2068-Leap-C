// Arithmetic on a struct.
// expect: error E_OPERAND 7
struct s { int a; };
struct s v;
int main(void)
{
    return v + 1; /*E*/
}
