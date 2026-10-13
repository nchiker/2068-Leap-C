// itoa with a base outside 2-36 is runtime error 4.
// expect: rterror 4
// rtline: 5
char s[20];
int main(void)
{
    itoa(5, s, 36);
    itoa(5, s, 37);
    return 0;
}
