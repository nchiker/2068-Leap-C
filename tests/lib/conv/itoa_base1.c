// itoa with base 1 (or 0, or negative) is runtime error 4, not an endless loop.
// expect: rterror 4
char s[20];
int main(void)
{
    itoa(5, s, 1);
    return 0;
}
