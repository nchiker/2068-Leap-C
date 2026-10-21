// itoa with base 0 is runtime error 4.
// expect: rterror 4
char s[20];
int main(void)
{
    itoa(5, s, 0);
    return 0;
}
