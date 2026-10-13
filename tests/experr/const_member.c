// A member of a const struct is const.
// expect: error E_CONST 7
struct s { int a; int b; };
const struct s v;
int main(void)
{
    v.b -= 1; /*E*/
    return 0;
}
