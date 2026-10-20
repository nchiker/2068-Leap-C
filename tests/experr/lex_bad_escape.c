// An unknown escape sequence in a string literal.
// expect: error E_ESCAPE 5
int main(void)
{
    char *s = "a\qb";
    return s[0];
}
