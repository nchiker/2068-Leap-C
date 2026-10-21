// itoa with a negative base is runtime error 4.
// expect: rterror 4
char s[20];
int main(void)
{
    itoa(5, s, -10);
    return 0;
}
