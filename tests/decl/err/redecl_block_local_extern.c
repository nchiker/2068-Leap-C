// expect: error E_REDECL 6
int g;
int main(void)
{
    int g;
    extern int g;
    return g;
}
