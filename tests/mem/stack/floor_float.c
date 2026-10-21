// The deepest run-time stack with floats (Phase 8), at the floor as floor_worst.c: 40 held int
// operands (80 B), then 9 held float operands (3-word slots, 54 B: counted with the pending argument
// words, at most 32) around printf's %.9f (4 words), whose float formatting is the float core's
// deepest path (34 B measured). ENTER's margin covers all of it: nothing below $F800 is written.
// expect: exit 41
// stacklow: $F800
// noaudit
// screen: 22 0.333333333
int one;
int *p;
float fone = 1;
float *q;
int worst(void)
{
    return *p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(
           *p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(*p+(
           (int)(*q+(*q+(*q+(*q+(*q+(*q+(*q+(*q+(*q+(printf("%.9f\n", *q / 3), 0.5)))))))))) != 0
           ))))))))))))))))))))))))))))))))))))))));
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
    q = &fone;
    at(23, 0);
    return deep(0);
}
