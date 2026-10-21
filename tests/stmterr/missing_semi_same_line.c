// Two statements on one line, the `;` between them missing.
// expect: error E_SYNTAX 6
int main(void)
{
    int x, y;
    x = 1 y = 2;
    return x + y;
}
