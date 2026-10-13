// expect: error E_BADCHAR 8
int main(void)
{
    int a;
    /* comment
       lines */
    a = 1;
    a = a @ 2;
}
