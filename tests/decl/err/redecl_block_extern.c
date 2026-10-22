// expect: error E_REDECL 6
int g;
int main(void)
{
    extern int g;
    int g;
    return g;
}
