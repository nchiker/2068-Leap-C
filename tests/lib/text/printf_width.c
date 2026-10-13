// printf widths right-align with spaces; a text longer than its width is printed whole; a
// width of 0 does nothing; %s and %c take widths too.
// expect: exit 0
// screen: 0     7:   -12:65535
// screen: 1 123456:abc:   ab:  Z
// screen: 2 0:x:            10 chars
int main(void)
{
    cls();
    printf("%5d:%6d:%3u\n", 7, -12, 65535);
    printf("%2d%d:%1s:%5s:%3c\n", 123, 456, "abc", "ab", 'Z');
    printf("%0d:%0s:%20s\n", 0, "x", "10 chars");
    return 0;
}
