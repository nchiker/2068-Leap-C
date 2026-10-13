// BREAK in the middle of printf's output (inside the platform's character renderer).
// expect: rterror 5
// rtline: 9
// break: after 500000
// breakpc: 0 0x4000
// noaudit
// rundepth: 1
// ay: 8=0 9=0 10=0
int main(void)
{
    int i;
    for (i = 0; ; i++)
        printf("%d %s ", i, "and more text");
    return 0;
}
