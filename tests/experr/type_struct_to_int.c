// A struct cannot be assigned to an int.
// expect: error E_TYPE 8
struct s { int a; };
struct s v;
int main(void)
{
    int x;
    x = v; /*E*/
    return 0;
}
