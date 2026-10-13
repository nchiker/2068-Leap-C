// printf: %d %u %x %c %s %% at their boundaries; text between the conversions.
// expect: exit 0
// screen: 0 0 -1 32767 -32768
// screen: 1 0 65535 32768
// screen: 2 0 ffff beef 7f
// screen: 3 Q:= text 100%
// screen: 4 %%end
int main(void)
{
    cls();
    printf("%d %d %d %d\n", 0, -1, 32767, -32768);
    printf("%u %u %u\n", 0, 65535, 32768);
    printf("%x %x %x %x\n", 0, -1, 0xBEEF, 127);
    printf("%c%c%c %s %d%%\n", 'Q', ':', '=', "text", 100);
    printf("%%%%end");
    return 0;
}
