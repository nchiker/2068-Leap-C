// expect: error E_OPERAND 5
int main(void)
{
    char *p;
    switch (p) { case 0: ; }
    return 0;
}
