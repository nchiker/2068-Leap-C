// The deepest run-time stack between two frame checks, at the floor (spec.md 5.3, 4.10;
// include/leapc_layout.inc): deep() recurses until its frame is just above the floor ($F900),
// then worst() evaluates 40 held operands (80 B) around a library call with 32 argument words
// pending (itoa's 2 and printf's 30: 64 B), whose printf scrolls the screen (the deepest library
// path). ENTER's margin covers all of it: nothing below $F800 (image region 3) is written.
// expect: exit 41
// stacklow: $F800
// noaudit
// screen: 22 12345678901234567890123456789
int one;
int *p;
char buf[8];
int worst(void)
{
    return *p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(
           *p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(
           *p+(*p+(*p+(*p+(*p+(
           itoa(printf("%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d%d\n",
                                1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2, 3, 4,
                                5, 6, 7, 8, 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
                           buf, 10) != 0))))))))))))))))))))))))))))))))))))))));
}
int deep(int n)
{
    char probe;
    if ((unsigned)&probe > 0xF910)        /* the next frame (7 bytes) stays above the floor */
        return deep(n + 1);
    return worst();
}
int main(void)
{
    one = 1;
    p = &one;
    at(23, 0);
    return deep(0);
}
