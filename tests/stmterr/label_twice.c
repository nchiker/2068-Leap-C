// expect: error E_REDEF 6
int main(void)
{
here:
    ;
here:
    return 0;
}
