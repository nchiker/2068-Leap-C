// ?: with a pointer and a float operand: TYPE MISMATCH (C89 6.3.15).
// expect: error E_TYPE 7
int k;
char *p;
int main(void)
{
    return k ? p : 1.5;
}
