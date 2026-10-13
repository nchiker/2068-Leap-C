// A pointer walk over a string literal: strlen.
// expect: exit 11
int len(char *s)
{
    char *p;
    p = s;
    while (*p) p++;
    return p - s;
}
int main(void) { return len("hello world"); }
