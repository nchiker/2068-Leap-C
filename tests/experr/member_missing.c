// No such member.
// expect: error E_MEMBER 7
struct s { int a; };
struct s v;
int main(void)
{
    return v.b; /*E*/
}
