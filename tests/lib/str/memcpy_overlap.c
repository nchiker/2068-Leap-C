// memcpy is memmove: overlapping copies are safe both ways (spec.md 7.1).
// expect: exit 0
// screen: 0 hhelloworld|ello worldd
char s[20] = "hello world";
char t[20] = "hello world";
int main(void)
{
    cls();
    memcpy(s + 1, s, 5);
    memcpy(t, t + 1, 10);
    printf("%s|%s\n", s, t);
    return 0;
}
