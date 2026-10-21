// printf: a conversion character it does not know prints the next argument as a character, and
// flags are not supported: in "%-3d" the '-' is that character, then "3d" is plain text (spec.md 7.1).
// expect: exit 0
// screen: 0 A|B3d|C
int main(void)
{
    cls();
    printf("%q|%-3d|%c\n", 65, 66, 67);
    return 0;
}
