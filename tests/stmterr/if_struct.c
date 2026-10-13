// expect: error E_OPERAND 6
struct s { int a; } v;
int main(void)
{
    int r;
    if (v) r = 1;
    return 0;
}
