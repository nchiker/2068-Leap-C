// Struct assignment is not supported (use pointers or copy members).
// expect: error E_NOTSUP 8
struct s { int a; };
struct s v;
struct s w;
int main(void)
{
    v = w; /*E*/
    return 0;
}
