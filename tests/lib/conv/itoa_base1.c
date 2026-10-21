// itoa with base 1 is runtime error 4, not an endless loop (base 0: itoa_base0.c; negative: itoa_base_negative.c).
// expect: rterror 4
char s[20];
int main(void)
{
    itoa(5, s, 1);
    return 0;
}
