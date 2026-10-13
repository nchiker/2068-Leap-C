// expect: error E_CONSTEXPR 5
int main(void)
{
    int a = 1;
    static int b = a;
    return b;
}
