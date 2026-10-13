// gets(buf, max) stores at most max - 1 characters; further keys are ignored until ENTER.
// max 1 (and less) reads an empty line.
// expect: exit 0
// keys: "ABCDEF" ENTER "QW" ENTER "R" ENTER
// screen: 0 ABC
char buf[8];
char guard[2];
int main(void)
{
    cls();
    guard[0] = 'G';
    gets(buf, 4);
    if (strcmp(buf, "ABC") != 0) return 1;
    gets(buf, 1);
    if (buf[0] != 0) return 2;
    gets(buf, -5);
    if (buf[0] != 0) return 3;
    if (guard[0] != 'G') return 4;
    return 0;
}
