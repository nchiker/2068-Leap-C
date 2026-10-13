// expect: error E_SYNTAX 5
int main(void)
{
    int i;
    for (i = 0; i < 3) i++;
    return 0;
}
