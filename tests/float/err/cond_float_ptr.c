// ?: with a float and a pointer operand: TYPE MISMATCH (C89 6.3.15).
// expect: error E_TYPE 7
int k;
char *p;
int main(void)
{
    return k ? 1.5 : p;
}
