// expect: error E_CASE 5
int main(void)
{
    switch (2) { case 1: ; }
    case 2: return 0;
}
