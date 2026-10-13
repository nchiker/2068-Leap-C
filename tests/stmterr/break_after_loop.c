// expect: error E_BREAK 6
int main(void)
{
    int i;
    for (i = 0; i < 3; i++) ;
    break;
}
