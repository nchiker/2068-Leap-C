// expect: error E_UNDEFLABEL 5
int main(void)
{
    int x;
    goto nowhere;
    x = 1;
    goto nowhere;
    return x;
}
