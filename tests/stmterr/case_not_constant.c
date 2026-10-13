// expect: error E_CONSTEXPR 6
int main(void)
{
    int x;
    x = 1;
    switch (x) { case x: ; }
    return 0;
}
